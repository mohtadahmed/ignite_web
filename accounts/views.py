from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from .serializers import RegisterSerializer
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import User, StudentProfile, Course, CourseAssignment, FacultyProfile, StudentCourseEnrollment
import csv
from django.http import HttpResponse
from .forms import CourseForm, CourseAssignmentForm, FacultyCreationForm, StudentCourseEnrollmentForm


# Create your views here.
User = get_user_model()
token_generator = PasswordResetTokenGenerator()

@login_required(login_url='login')
def dashboard(request):
    total_users = User.objects.count()
    total_students = User.objects.filter(role='student').count()
    total_faculty = User.objects.filter(role='faculty').count()

    context = {
        'total_users': total_users,
        'total_students': total_students,
        'total_faculty': total_faculty,
    }
    return render(request, 'dashboard.html', context)


@login_required
def faculty_dashboard(request):
    user = request.user
    
    # Ensure the user is faculty role
    if user.role != 'faculty':
        return render(request, '404.html')  # or redirect or show error
    
    try:
        faculty_profile = FacultyProfile.objects.get(user=user)
    except FacultyProfile.DoesNotExist:
        return render(request, 'error.html', {'message': 'Faculty profile not found.'})
    
    # Get courses assigned to this faculty
    assigned_courses = CourseAssignment.objects.filter(faculty=faculty_profile).select_related('course')
    
    # Count of assigned courses
    total_assigned_courses = assigned_courses.count()
    
    # Get course IDs
    course_ids = assigned_courses.values_list('course_id', flat=True)
    
    # Count total students enrolled in those courses
    total_students = StudentCourseEnrollment.objects.filter(course__in=course_ids).values('student').distinct().count()
    
    context = {
        'total_assigned_courses': total_assigned_courses,
        'total_students': total_students,
        'assigned_courses': assigned_courses,  # optional to list in template
    }
    return render(request, 'faculty_dashboard.html', context)


@login_required
def student_dashboard(request):
    return render(request, 'student_dashboard.html')
    


@api_view(['POST'])
def register_user(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'User registered successfully.'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def register_view(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        repeat_password = request.POST.get('repeat_password')

        if not full_name or not email or not password or not repeat_password:
            messages.error(request, 'All fields are required.')
            return redirect('register')
        
        if password != repeat_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return redirect('register')

        # Split full name
        first_name, last_name = full_name.split(' ', 1) if ' ' in full_name else (full_name, '')

        # Create user
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        user.save()

        messages.success(request, 'User registered successfully!')
        return redirect('register')
    
    return render(request, 'register.html')



@api_view(['POST'])
def login_user(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)

    if user is not None:
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
            }
        })
    else:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not email or not password:
            messages.error(request, 'All fields are required.')
            return redirect('login')

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)

            # Redirect based on user role
            if user.role == 'admin':
                return redirect('dashboard')  # admin dashboard
            elif user.role == 'faculty':
                return redirect('faculty_dashboard')  # faculty dashboard
            elif user.role == 'student':
                return redirect('student_dashboard')  # optional student dashboard
            else:
                return redirect('student_dashboard')  # default fallback
        else:
            messages.error(request, 'Invalid credentials.')
            return redirect('login')

    return render(request, 'login.html')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    try:
        refresh_token = request.data['refresh']
        token = RefreshToken(refresh_token)
        token.blacklist()

        return Response({'message': 'Logout successful'}, status=status.HTTP_205_RESET_CONTENT)
    except KeyError:
        return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)
    except TokenError:
        return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)


@login_required
def logout_view(request):

    logout(request)
    return redirect('login')  # Redirect to login after logout
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reset_password(request):
    user = request.user
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')

    if not old_password or not new_password:
        return Response({'error': 'Old and new passwords are required'}, status=status.HTTP_400_BAD_REQUEST)

    if not user.check_password(old_password):
        return Response({'error': 'Old password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()

    return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)


@api_view(['POST'])
def request_password_reset(request):
    email = request.data.get('email')
    if not email:
        return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)
        reset_link = f"http://localhost:3000/reset-password/{uid}/{token}/"  # Update with your frontend route

        send_mail(
            subject='Password Reset Request',
            message=f"Click the link to reset your password: {reset_link}",
            from_email=None,
            recipient_list=[email],
        )

        return Response({'message': 'Password reset link sent to your email'}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({'error': 'No user with this email'}, status=status.HTTP_404_NOT_FOUND)
    

@api_view(['POST'])
def reset_password_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError):
        return Response({'error': 'Invalid link'}, status=status.HTTP_400_BAD_REQUEST)

    if not token_generator.check_token(user, token):
        return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)

    new_password = request.data.get('new_password')
    if not new_password:
        return Response({'error': 'New password is required'}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()
    return Response({'message': 'Password has been reset successfully'}, status=status.HTTP_200_OK)



# Access check
def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

# List/Search Students
@login_required
def student_list(request):
    query = request.GET.get('q')
    if query:
        students = StudentProfile.objects.filter(user__email__icontains=query)
    else:
        students = StudentProfile.objects.all()
    return render(request, 'students/student_list.html', {'students': students})


# Add Student
@login_required
def add_student(request):
    if request.method == 'POST':
        print('data', request.body)
        email = request.POST.get('email')
        password = request.POST.get('password')
        student_id = request.POST.get('student_id')
        department = request.POST.get('department')
        semester = request.POST.get('semester')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        session = request.POST.get('session')
        program = request.POST.get('program')

        print("Parsed POST data:")
        print("Email:", email)
        print("Password:", password)
        print("Student ID:", student_id)

        if User.objects.filter(email=email).exists():
            print("⚠️ Email already exists:", email)
            messages.error(request, "Email already exists.")
            return redirect('add_student')

        try:
            user = User.objects.create(
                email=email,
                role='student',
            )
            user.set_password(password)
            user.save()
            print("✅ User created:", user.email)

            StudentProfile.objects.create(
                user=user,
                student_id=student_id,
                department=department,
                semester=semester,
                phone=phone,
                address=address,
                session=session,
                program=program
            )
            print("Student profile created for:", user.email)

            messages.success(request, "Student added successfully.")
        except Exception as e:
            print("Error occurred:", str(e))
            messages.error(request, "Something went wrong while creating student.")
        return redirect('student_list')

    return render(request, 'students/add_students.html')


@login_required
def download_sample_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sample_students.csv"'

    writer = csv.writer(response)
    writer.writerow(['email', 'password', 'student_id', 'department', 'semester', 'phone', 'session', 'address', 'program'])
    writer.writerow(['john@example.com', '123456', 'ST001', 'CSE', '6', '0123456789', '2020-21', 'Dhaka', 'B.Sc'])
    writer.writerow(['jane@example.com', 'abcdef', 'ST002', 'EEE', '4', '0987654321', '2021-22', 'Chittagong', 'M.S'])

    return response


@login_required
def student_bulk_upload(request):
    if request.method == 'POST':
        csv_file = request.FILES.get('file')
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'This is not a CSV file.')
            return redirect('student_bulk_upload')

        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)

        for row in reader:
            email = row['email']
            password = row['password']
            student_id = row['student_id']
            department = row.get('department', '')
            semester = row.get('semester', '')
            phone = row.get('phone', '')
            session = row.get('session', '')
            address = row.get('address', '')
            program = row.get('program', '')

            user, created = User.objects.get_or_create(email=email)
            if created:
                user.set_password(password)
                user.save()

            StudentProfile.objects.update_or_create(
                user=user,
                defaults={
                    'student_id': student_id,
                    'department': department,
                    'semester': semester,
                    'phone': phone,
                    'session': session,
                    'address': address,
                    'program': program,
                }
            )

        messages.success(request, "Students uploaded successfully.")
        return redirect('student_list')

    return render(request, 'students/student_bulk_upload.html')


# Edit Student
@login_required
def edit_student(request, student_id):
    profile = get_object_or_404(StudentProfile, id=student_id)
    user = profile.user

    if request.method == 'POST':
        email = request.POST.get('email')
        student_id = request.POST.get('student_id')
        department = request.POST.get('department')
        semester = request.POST.get('semester')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        session = request.POST.get('session')
        program = request.POST.get('program')

        user.email = email
        user.save()

        profile.student_id = student_id
        profile.department = department
        profile.semester = semester
        profile.phone = phone
        profile.address = address
        profile.session = session
        profile.program = program
        profile.save()

        messages.success(request, "Student updated successfully.")
        return redirect('student_list')

    return render(request, 'students/edit_student.html', {'profile': profile})


# Delete Student
@login_required
@user_passes_test(is_admin)
def delete_student(request, student_id):
    profile = get_object_or_404(StudentProfile, id=student_id)
    user = profile.user
    user.delete()
    messages.success(request, "Student deleted successfully.")
    return redirect('student_list')


# Courses Section
# Course add view
def course_add(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('course_list')
    else:
        form = CourseForm()
    return render(request, 'courses/course_add.html', {'form': form})

# Course list view
def course_list(request):
    courses = Course.objects.all()
    return render(request, 'courses/course_list.html', {'courses': courses})


def assign_faculty_to_course(request):
    if request.method == 'POST':
        form = CourseAssignmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('assigned_courses_list')
    else:
        form = CourseAssignmentForm()
    return render(request, 'courses/assign_faculty.html', {'form': form})

def assigned_courses_list(request):
    assignments = CourseAssignment.objects.select_related('course', 'faculty').all()
    return render(request, 'courses/assigned_courses_list.html', {'assignments': assignments})


# Faculty Create
def create_faculty(request):
    if request.method == 'POST':
        form = FacultyCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('faculty_list')
    else:
        form = FacultyCreationForm()
    return render(request, 'faculty/create_faculty.html', {'form': form})


def faculty_list(request):
    faculties = User.objects.filter(role='faculty')
    return render(request, 'faculty/faculty_list.html', {'faculties': faculties})


@login_required
def assign_courses_to_student(request):
    if request.method == 'POST':
        form = StudentCourseEnrollmentForm(request.POST)
        if form.is_valid():
            student = form.cleaned_data['student']
            courses = form.cleaned_data['courses']
            
            # Remove existing enrollments (optional: for full overwrite)
            StudentCourseEnrollment.objects.filter(student=student).delete()
            
            # Add new enrollments
            for course in courses:
                StudentCourseEnrollment.objects.create(student=student, course=course)

            return render(request, 'success.html', {'message': 'Courses assigned successfully!'})
    else:
        form = StudentCourseEnrollmentForm()
    
    return render(request, 'courses/assign_courses.html', {'form': form})