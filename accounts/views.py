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
from academics.models import Semester, Routine, ScheduleItem, CourseResource
import csv
from django.http import HttpResponse
from .forms import CourseForm, CourseAssignmentForm, FacultyCreationForm, StudentCourseEnrollmentForm
import pandas as pd
from django.http import FileResponse, Http404
import os
from django.conf import settings
from io import BytesIO


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

    
    schedule_items = ScheduleItem.objects.all().order_by('scheduled_date')
    resources = CourseResource.objects.all().order_by('-uploaded_at')[:10]
    
    context = {
        'total_assigned_courses': total_assigned_courses,
        'total_students': total_students,
        'assigned_courses': assigned_courses,  # optional to list in template
        'schedule_items': schedule_items,
        'resources': resources,
    }
    return render(request, 'faculty_dashboard.html', context)


@login_required
def student_dashboard(request):
    context = {
        'routine': Routine.objects.last(),
        'schedule_items': ScheduleItem.objects.order_by('scheduled_date'),
        'resources': CourseResource.objects.order_by('-uploaded_at')[:10]
    }
    return render(request, 'student_dashboard.html', context)
    


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
    students = StudentProfile.objects.all()
    return render(request, 'students/student_list.html', {'students': students})


# Add Student
@login_required
def add_student(request):
    if request.method == "POST":
        # Collect form data
        student_id = request.POST.get('student_id')
        email = request.POST.get('email')
        department = request.POST.get('department')
        semester_id = request.POST.get('semester')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        session = request.POST.get('session')
        program = request.POST.get('program')
        password = request.POST.get('password')

        try:
            user = User.objects.create(
                email=email,
                role='student',
            )
            user.set_password(password)
            user.save()

            semester = Semester.objects.get(id=semester_id)

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

            messages.success(request, "Student added successfully.")
            return redirect('add_student')

        except Semester.DoesNotExist:
            messages.error(request, "Invalid semester selected.")
        except Exception as e:
            messages.error(request, f"Something went wrong: {e}")

    semesters = Semester.objects.all()
    return render(request, 'students/add_students.html', {'semesters': semesters})


@login_required
def download_sample_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sample_students.csv"'

    writer = csv.writer(response)
    writer.writerow(['email', 'password', 'student_id', 'department', 'semester', 'phone', 'session', 'address', 'program'])
    writer.writerow(['john@example.com', '123456', 'ST001', 'CSE', '2-1', '0123456789', '2020-21', 'Dhaka', 'B.Sc'])
    writer.writerow(['jane@example.com', '123456', 'ST002', 'EEE', '4-1', '0987654321', '2021-22', 'Chittagong', 'M.S'])

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
            try:
                email = row['email']
                password = row['password']
                student_id = row['student_id']
                department = row.get('department', '')
                semester_str = row.get('semester', '')
                phone = row.get('phone', '')
                session = row.get('session', '')
                address = row.get('address', '')
                program = row.get('program', '')

                # Get or create user
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={'role': 'student'}
                )
                if created:
                    user.set_password(password)
                    user.save()

                # Get or create semester instance
                semester = None
                if semester_str:
                    semester, _ = Semester.objects.get_or_create(name=semester_str)

                # Create or update student profile
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

            except Exception as e:
                messages.error(request, f"Error processing student {row.get('student_id', 'unknown')}: {str(e)}")
                continue

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
        course_code = request.POST.get('course_code')
        course_name = request.POST.get('course_name')
        credit = request.POST.get('credit')
        semester_id = request.POST.get('semester')
        department = request.POST.get('department')
        course_type = request.POST.get('course_type')

        try:
            semester = Semester.objects.get(id=semester_id)

            Course.objects.create(
                course_code=course_code,
                course_name=course_name,
                credit=credit,
                semester=semester,
                department=department,
                course_type=course_type
            )
            messages.success(request, "Course added successfully.")
            return redirect('course_list')
        except Semester.DoesNotExist:
            messages.error(request, "Invalid semester selected.")
        except Exception as e:
            messages.error(request, f"Error adding course: {e}")

    semesters = Semester.objects.all()
    # course_types = [choice[0] for choice in Course.COURSE_TYPE_CHOICES]
    course_types = Course.COURSE_TYPE_CHOICES
    return render(request, 'courses/course_add.html', {'semesters': semesters, 'course_types': course_types})

# Course list view
def course_list(request):
    courses = Course.objects.all()
    return render(request, 'courses/course_list.html', {'courses': courses})


def course_bulk_upload(request):
    if request.method == 'POST' and request.FILES.get('upload_file'):
        file = request.FILES['upload_file']
        try:
            # Read file into DataFrame
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)

            # Normalize column names
            df.columns = df.columns.str.strip()

            required_columns = ['Course Code', 'Course Name', 'Credit', 'Course Type', 'Department', 'Semester']
            for col in required_columns:
                if col not in df.columns:
                    messages.error(request, f"Missing required column: {col}")
                    return redirect('course_bulk_upload')

            for _, row in df.iterrows():
                semester_name = str(row['Semester']).strip()
                semester_obj, _ = Semester.objects.get_or_create(name=semester_name)

                Course.objects.update_or_create(
                    course_code=str(row['Course Code']).strip(),
                    defaults={
                        'course_name': str(row['Course Name']).strip(),
                        'credit': float(row['Credit']),
                        'course_type': str(row['Course Type']).strip().lower(),  # 'theory' or 'lab'
                        'department': str(row['Department']).strip(),
                        'semester': semester_obj
                    }
                )
            messages.success(request, "Courses uploaded successfully.")
        except Exception as e:
            messages.error(request, f"Upload failed: {str(e)}")
        return redirect('course_bulk_upload')

    return render(request, 'courses/course_bulk_upload.html')



def download_course_template(request):
    file_path = os.path.join(settings.BASE_DIR, 'static', 'uploads', 'course_template.xlsx')
    
    if not os.path.exists(file_path):
        raise Http404("Template not found.")
    
    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename='course_template.xlsx')


def assign_faculty_to_course(request):
    courses = Course.objects.all()
    faculties = FacultyProfile.objects.select_related('user').all()

    if request.method == 'POST':
        if 'upload_excel' in request.POST:
            excel_file = request.FILES.get('excel_file')
            if not excel_file:
                return render(request, 'courses/assign_faculty.html', {
                    'courses': courses, 'faculties': faculties,
                    'error': 'No file uploaded'
                })

            try:
                df = pd.read_excel(excel_file)
                for _, row in df.iterrows():
                    course_code = str(row['course_code']).strip()
                    faculty_email = str(row['faculty_email']).strip()

                    try:
                        course = Course.objects.get(course_code=course_code)
                        faculty = FacultyProfile.objects.select_related('user').get(user__email=faculty_email)
                        CourseAssignment.objects.get_or_create(course=course, faculty=faculty)
                    except Course.DoesNotExist:
                        messages.error(request, f"Course not found: {course_code}")
                    except FacultyProfile.DoesNotExist:
                        messages.error(request, f"Faculty not found: {faculty_email}")

                messages.success(request, "Faculty assignments uploaded successfully.")
                return redirect('assigned_courses_list')

            except Exception as e:
                return render(request, 'courses/assign_faculty.html', {
                    'courses': courses, 'faculties': faculties,
                    'error': str(e)
                })

        else:
            # manual form post
            course_id = request.POST.get('course_id')
            faculty_id = request.POST.get('faculty_id')

            try:
                course = Course.objects.get(id=course_id)
                faculty = FacultyProfile.objects.get(id=faculty_id)
                CourseAssignment.objects.get_or_create(course=course, faculty=faculty)
                messages.success(request, "Course assigned successfully.")
                return redirect('assigned_courses_list')
            except Exception as e:
                messages.error(request, f"Error: {e}")

    return render(request, 'courses/assign_faculty.html', {
        'courses': courses,
        'faculties': faculties
    })

def assigned_courses_list(request):
    assignments = CourseAssignment.objects.select_related('course', 'faculty').all()
    return render(request, 'courses/assigned_courses_list.html', {'assignments': assignments})

def edit_course_assignment(request, assignment_id):
    assignment = get_object_or_404(CourseAssignment, id=assignment_id)
    if request.method == 'POST':
        course_id = request.POST.get('course')
        faculty_id = request.POST.get('faculty')

        assignment.course_id = course_id
        assignment.faculty_id = faculty_id
        assignment.save()
        return redirect('assigned_courses_list')

    courses = Course.objects.all()
    faculty_members = FacultyProfile.objects.all()
    return render(request, 'courses/edit_assigned_course.html', {
        'assignment': assignment,
        'courses': courses,
        'faculty_members': faculty_members
    })

def delete_course_assignment(request, assignment_id):
    assignment = get_object_or_404(CourseAssignment, id=assignment_id)
    assignment.delete()
    return redirect('assigned_courses_list')



# Faculty Create
def create_faculty(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'A user with this email already exists.')
        elif not email or not password:
            messages.error(request, 'Email and password are required.')
        else:
            user = User.objects.create_user(
                email=email,
                password=password,
                role='faculty'
            )
            FacultyProfile.objects.create(user=user)
            messages.success(request, 'Faculty created successfully.')
            return redirect('faculty_list')

    return render(request, 'faculty/create_faculty.html')


def faculty_list(request):
    faculties = User.objects.filter(role='faculty').select_related('facultyprofile')
    print('faculties', faculties)
    return render(request, 'faculty/faculty_list.html', {'faculties': faculties})


# Edit Faculty
def edit_faculty(request, faculty_id):
    user = get_object_or_404(User, id=faculty_id, role='faculty')
    print('user', user)

    faculty = FacultyProfile.objects.get(user=user)
    print('faculty', faculty)
    if request.method == 'POST':
        print('data', request.POST)
        faculty.name = request.POST.get('name')
        faculty.designation = request.POST.get('designation')
        faculty.department = request.POST.get('department')
        faculty.email = request.POST.get('email')
        faculty.save()
        return redirect('faculty_list')
    return render(request, 'faculty/edit_faculty.html', {'faculty': faculty})


# Delete Faculty
def delete_faculty(request, faculty_id):
    faculty = get_object_or_404(User, id=faculty_id, role='faculty')
    faculty.delete()
    return redirect('faculty_list')


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


# Student Migration
@login_required
def semester_migration_panel(request):
    semesters = Semester.objects.all()
    students = []

    if request.method == 'POST':
        print('POST data:', request.POST)
        current_sem_id = request.POST.get('current_semester')
        next_sem_id = request.POST.get('next_semester')
        student_ids = request.POST.getlist('student_ids')

        current_sem = Semester.objects.get(id=current_sem_id)
        next_sem = Semester.objects.get(id=next_sem_id)

        selected_students = StudentProfile.objects.filter(id__in=student_ids)

        for student in selected_students:
            student.semester = next_sem
            student.migrated_semesters.add(current_sem)
            student.save()

        messages.success(request, f"{selected_students.count()} students migrated to {next_sem.name} successfully.")
        return redirect('semester_migration_panel')

    elif request.method == 'GET' and 'semester_filter' in request.GET:
        print('GET data:', request.GET)
        selected_semester = request.GET.get('semester_filter')
        if selected_semester:
            students = StudentProfile.objects.filter(semester=selected_semester)

    return render(request, 'students/semester_migration_panel.html', {
        'semesters': semesters,
        'students': students,
    })