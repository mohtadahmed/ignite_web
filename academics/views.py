from django.shortcuts import render, redirect
from .models import *
import os
from django.conf import settings
from django.contrib import messages
from django.utils.timezone import now
from django.utils import timezone
import glob
from django.contrib.auth.decorators import login_required

# Create your views here.
def generic_base(request):
    return render(request, 'generic_base.html')


def upload_routine(request):
    if request.method == 'POST' and request.FILES.get('routine_pdf'):
        routine_pdf = request.FILES['routine_pdf']
        upload_dir = os.path.join(settings.BASE_DIR, 'static', 'uploads', 'routine')
        os.makedirs(upload_dir, exist_ok=True)  # Create folder if not exists

        filename = f"routine_{now().strftime('%Y%m%d%H%M%S')}.pdf"
        file_path = os.path.join(upload_dir, filename)

        with open(file_path, 'wb+') as destination:
            for chunk in routine_pdf.chunks():
                destination.write(chunk)

        messages.success(request, "Routine PDF uploaded successfully!")
        return redirect('view_routines')

    return render(request, 'academics/upload_routine.html')

def view_routines(request):
    routine_folder = os.path.join(settings.BASE_DIR, 'static', 'uploads', 'routine')
    routine_files = glob.glob(os.path.join(routine_folder, '*.pdf'))

    latest_file = None
    if routine_files:
        latest_file = max(routine_files, key=os.path.getctime)
        latest_file = str(latest_file).replace(str(settings.BASE_DIR), '')  # Fix here
        latest_file = latest_file.replace('\\', '/')  # Optional: for web URLs on Windows

    return render(request, 'academics/view_routine.html', {'routine_pdf': latest_file})


@login_required
def upload_resource(request):
    if request.method == 'POST':
        course_id = request.POST.get('course')
        category = request.POST.get('category')
        title = request.POST.get('title')
        description = request.POST.get('description')
        file = request.FILES.get('file')
        external_link = request.POST.get('external_link')

        course = Course.objects.get(id=course_id)

        CourseResource.objects.create(
            course=course,
            uploaded_by=request.user,
            category=category,
            title=title,
            description=description,
            file=file,
            external_link=external_link
        )

        messages.success(request, "Resource uploaded successfully.")
        return redirect('upload_resource')

    courses = Course.objects.all()
    return render(request, 'academics/upload_resource.html', {'courses': courses})


def resource_library(request):
    resources = CourseResource.objects.select_related('course').order_by('-uploaded_at')
    return render(request, 'academics/resource_library.html', {'resources': resources})


from django.http import FileResponse, Http404

def download_file(request, file_path):
    filepath = os.path.join(settings.MEDIA_ROOT, file_path)
    if os.path.exists(filepath):
        return FileResponse(open(filepath, 'rb'), as_attachment=True)
    raise Http404("File not found.")


@login_required
def add_schedule(request):
    if request.method == 'POST':
        course_id = request.POST['course']
        exam_type = request.POST['exam_type']
        scheduled_date = request.POST['scheduled_date']

        ScheduleItem.objects.create(
            course_id=course_id,
            exam_type=exam_type,
            scheduled_date=scheduled_date,
            faculty=request.user
        )
        messages.success(request, "Schedule added successfully.")
        return redirect('faculty_schedule_list')

    courses = Course.objects.all()
    return render(request, 'academics/faculty_schedule_form.html', {'courses': courses})


@login_required
def student_schedule_list(request):
    schedules = ScheduleItem.objects.filter(scheduled_date__gte=timezone.now()).order_by('scheduled_date')
    return render(request, 'academics/student_schedule_list.html', {'schedules': schedules})