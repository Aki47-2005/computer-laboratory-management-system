from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from .models import Lab, Computer, Specification, Instructor, Schedule, Attendant, Maintenance, Disposal


def admin_required(view_func):
    """
    Decorator for views that checks that the user is logged in and is a staff member or superuser.
    Regular view-only users are redirected to the user_dashboard with an alert.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, 'Permission denied: This action is restricted to administrators. You have view-only access.')
            return redirect('user_dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@login_required
def index(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('user_dashboard')
    context = {
        'lab_count': Lab.objects.count(),
        'computer_count': Computer.objects.count(),
        'instructor_count': Instructor.objects.count(),
        'attendant_count': Attendant.objects.count(),
        'schedule_count': Schedule.objects.count(),
        'active_count': Computer.objects.filter(status='Active').count(),
        'maintenance_count': Computer.objects.filter(status='Maintenance').count(),
        'disposed_count': Computer.objects.filter(status='Disposed').count(),
        'recent_schedules': Schedule.objects.select_related('lab', 'instructor').order_by('-id')[:5],
        'recent_maintenance': Maintenance.objects.select_related('computer').order_by('-date', '-id')[:5],
    }
    return render(request, 'index.html', context)


@login_required
def user_dashboard(request):
    all_labs = Lab.objects.all()
    all_computers = Computer.objects.select_related('lab').prefetch_related('specification_set').all()
    all_schedules = Schedule.objects.select_related('lab', 'instructor').order_by('day', 'start_time')
    all_instructors = Instructor.objects.all()
    all_attendants = Attendant.objects.select_related('lab').all()
    all_maintenance = Maintenance.objects.select_related('computer', 'computer__lab').order_by('-date', '-id')[:15]

    computers_list = []
    for comp in all_computers:
        comp.spec = comp.specification_set.first()
        computers_list.append(comp)

    labs_data = []
    for lab in all_labs:
        lab_pcs = [c for c in computers_list if c.lab_id == lab.id]
        total_pcs = len(lab_pcs)
        active_pcs = len([c for c in lab_pcs if c.status == 'Active'])
        maintenance_pcs = len([c for c in lab_pcs if c.status == 'Maintenance'])
        occupancy_pct = int((total_pcs / lab.capacity * 100)) if lab.capacity else 0
        labs_data.append({
            'lab': lab,
            'total_pcs': total_pcs,
            'active_pcs': active_pcs,
            'maintenance_pcs': maintenance_pcs,
            'occupancy_pct': min(occupancy_pct, 100),
        })

    context = {
        'total_labs': all_labs.count(),
        'total_computers': all_computers.count(),
        'active_computers': all_computers.filter(status='Active').count(),
        'maintenance_computers': all_computers.filter(status='Maintenance').count(),
        'total_schedules': all_schedules.count(),
        'total_instructors': all_instructors.count(),
        'total_attendants': all_attendants.count(),
        'labs_data': labs_data,
        'computers': computers_list,
        'schedules': all_schedules,
        'instructors': all_instructors,
        'attendants': all_attendants,
        'maintenance_records': all_maintenance,
    }
    return render(request, 'user_dashboard.html', context)


def login_page(request):
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST['username'],
            password=request.POST['password'],
        )
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', '')
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            if user.is_staff or user.is_superuser:
                return redirect('index')
            return redirect('user_dashboard')
        return render(request, 'login.html', {'error': 'Invalid username or password.'})
    return render(request, 'login.html')


def signup_page(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    for field in form.fields.values():
        field.widget.attrs['class'] = 'input-control'
    return render(request, 'signup.html', {'form': form})


def logout_page(request):
    if request.method == 'POST':
        logout(request)
    return redirect('login')


@login_required
def labs(request):
    if request.method == 'POST':
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, 'Permission denied: View-only users cannot add labs.')
            return redirect('labs')
        Lab.objects.create(
            name=request.POST['name'],
            location=request.POST['location'],
            capacity=request.POST['capacity'],
            duration=request.POST['duration'],
        )
        messages.success(request, 'Lab has been added successfully.')
        return redirect('labs')
    all_labs = Lab.objects.all()
    return render(request, 'labs.html', {'labs': all_labs})


@admin_required
def edit_lab(request, id):
    lab = get_object_or_404(Lab, id=id)
    if request.method == 'POST':
        lab.name = request.POST['name']
        lab.location = request.POST['location']
        lab.capacity = request.POST['capacity']
        lab.duration = request.POST['duration']
        lab.save()
        messages.success(request, 'Lab has been updated successfully.')
        return redirect('labs')
    return render(request, 'edit_lab.html', {'lab': lab})


@admin_required
def delete_lab(request, id):
    lab = get_object_or_404(Lab, id=id)
    if request.method == 'POST':
        lab.delete()
        messages.success(request, 'Lab has been deleted successfully.')
    return redirect('labs')


@login_required
def computers(request):
    if request.method == 'POST':
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, 'Permission denied: View-only users cannot add computers.')
            return redirect('computers')
        Computer.objects.create(
            name=request.POST['name'],
            brand=request.POST['brand'],
            type=request.POST['type'],
            colour=request.POST['colour'],
            lab_id=request.POST['lab'],
            status=request.POST['status'],
        )
        messages.success(request, 'Computer has been added successfully.')
        return redirect('computers')
    all_computers = Computer.objects.all()
    all_labs = Lab.objects.all()
    return render(request, 'computers.html', {'computers': all_computers, 'labs': all_labs})


@admin_required
def edit_computer(request, id):
    computer = get_object_or_404(Computer, id=id)
    if request.method == 'POST':
        computer.name = request.POST['name']
        computer.brand = request.POST['brand']
        computer.type = request.POST['type']
        computer.colour = request.POST['colour']
        computer.lab_id = request.POST['lab']
        computer.status = request.POST['status']
        computer.save()
        messages.success(request, 'Computer has been updated successfully.')
        return redirect('computers')
    all_labs = Lab.objects.all()
    return render(request, 'edit_computer.html', {'computer': computer, 'labs': all_labs})


@admin_required
def delete_computer(request, id):
    computer = get_object_or_404(Computer, id=id)
    if request.method == 'POST':
        computer.delete()
        messages.success(request, 'Computer has been deleted successfully.')
    return redirect('computers')


@login_required
def specifications(request):
    if request.method == 'POST':
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, 'Permission denied: View-only users cannot add specifications.')
            return redirect('specifications')
        Specification.objects.create(
            computer_id=request.POST['computer'],
            processor=request.POST['processor'],
            ram=request.POST['ram'],
            storage=request.POST['storage'],
            operating_system=request.POST['operating_system'],
        )
        messages.success(request, 'Specification has been added successfully.')
        return redirect('specifications')
    all_specs = Specification.objects.all()
    all_computers = Computer.objects.all()
    return render(request, 'specifications.html', {'specifications': all_specs, 'computers': all_computers})


@admin_required
def edit_specification(request, id):
    spec = get_object_or_404(Specification, id=id)
    if request.method == 'POST':
        spec.computer_id = request.POST['computer']
        spec.processor = request.POST['processor']
        spec.ram = request.POST['ram']
        spec.storage = request.POST['storage']
        spec.operating_system = request.POST['operating_system']
        spec.save()
        messages.success(request, 'Specification has been updated successfully.')
        return redirect('specifications')
    all_computers = Computer.objects.all()
    return render(request, 'edit_specification.html', {'spec': spec, 'computers': all_computers})


@admin_required
def delete_specification(request, id):
    spec = get_object_or_404(Specification, id=id)
    if request.method == 'POST':
        spec.delete()
        messages.success(request, 'Specification has been deleted successfully.')
    return redirect('specifications')


@login_required
def instructors(request):
    if request.method == 'POST':
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, 'Permission denied: View-only users cannot add instructors.')
            return redirect('instructor')
        Instructor.objects.create(
            full_name=request.POST['full_name'],
            phone=request.POST['phone'],
            email=request.POST['email'],
            department=request.POST['department'],
        )
        messages.success(request, 'Instructor has been added successfully.')
        return redirect('instructor')
    all_instructors = Instructor.objects.all()
    return render(request, 'instructor.html', {'instructors': all_instructors})


@admin_required
def edit_instructor(request, id):
    instructor = get_object_or_404(Instructor, id=id)
    if request.method == 'POST':
        instructor.full_name = request.POST['full_name']
        instructor.phone = request.POST['phone']
        instructor.email = request.POST['email']
        instructor.department = request.POST['department']
        instructor.save()
        messages.success(request, 'Instructor has been updated successfully.')
        return redirect('instructor')
    return render(request, 'edit_instructor.html', {'instructor': instructor})


@admin_required
def delete_instructor(request, id):
    instructor = get_object_or_404(Instructor, id=id)
    if request.method == 'POST':
        instructor.delete()
        messages.success(request, 'Instructor has been deleted successfully.')
    return redirect('instructor')


@login_required
def schedules(request):
    if request.method == 'POST':
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, 'Permission denied: View-only users cannot add schedules.')
            return redirect('schedules')
        Schedule.objects.create(
            lab_id=request.POST['lab'],
            day=request.POST['day'],
            start_time=request.POST['start_time'],
            end_time=request.POST['end_time'],
            instructor_id=request.POST['instructor'],
        )
        messages.success(request, 'Schedule has been added successfully.')
        return redirect('schedules')
    all_schedules = Schedule.objects.all()
    all_labs = Lab.objects.all()
    all_instructors = Instructor.objects.all()
    return render(request, 'schedules.html', {'schedules': all_schedules, 'labs': all_labs, 'instructors': all_instructors})


@admin_required
def edit_schedule(request, id):
    schedule = get_object_or_404(Schedule, id=id)
    if request.method == 'POST':
        schedule.lab_id = request.POST['lab']
        schedule.day = request.POST['day']
        schedule.start_time = request.POST['start_time']
        schedule.end_time = request.POST['end_time']
        schedule.instructor_id = request.POST['instructor']
        schedule.save()
        messages.success(request, 'Schedule has been updated successfully.')
        return redirect('schedules')
    all_labs = Lab.objects.all()
    all_instructors = Instructor.objects.all()
    return render(request, 'edit_schedule.html', {'schedule': schedule, 'labs': all_labs, 'instructors': all_instructors})


@admin_required
def delete_schedule(request, id):
    schedule = get_object_or_404(Schedule, id=id)
    if request.method == 'POST':
        schedule.delete()
        messages.success(request, 'Schedule has been deleted successfully.')
    return redirect('schedules')


@login_required
def attendants(request):
    if request.method == 'POST':
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, 'Permission denied: View-only users cannot add attendants.')
            return redirect('attendants')
        Attendant.objects.create(
            full_name=request.POST['full_name'],
            phone=request.POST['phone'],
            lab_id=request.POST['lab'],
            shift=request.POST['shift'],
        )
        messages.success(request, 'Attendant has been added successfully.')
        return redirect('attendants')
    all_attendants = Attendant.objects.all()
    all_labs = Lab.objects.all()
    return render(request, 'attendants.html', {'attendants': all_attendants, 'labs': all_labs})


@admin_required
def edit_attendant(request, id):
    attendant = get_object_or_404(Attendant, id=id)
    if request.method == 'POST':
        attendant.full_name = request.POST['full_name']
        attendant.phone = request.POST['phone']
        attendant.lab_id = request.POST['lab']
        attendant.shift = request.POST['shift']
        attendant.save()
        messages.success(request, 'Attendant has been updated successfully.')
        return redirect('attendants')
    all_labs = Lab.objects.all()
    return render(request, 'edit_attendant.html', {'attendant': attendant, 'labs': all_labs})


@admin_required
def delete_attendant(request, id):
    attendant = get_object_or_404(Attendant, id=id)
    if request.method == 'POST':
        attendant.delete()
        messages.success(request, 'Attendant has been deleted successfully.')
    return redirect('attendants')


@login_required
def maintenance(request):
    if request.method == 'POST':
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, 'Permission denied: View-only users cannot add maintenance records.')
            return redirect('maintenance')
        Maintenance.objects.create(
            computer_id=request.POST['computer'],
            item=request.POST['item'],
            quantity=request.POST['quantity'],
            date=request.POST['date'],
            cost=request.POST['cost'],
        )
        messages.success(request, 'Maintenance record has been added successfully.')
        return redirect('maintenance')
    all_records = Maintenance.objects.all()
    all_computers = Computer.objects.all()
    return render(request, 'maintenance.html', {'records': all_records, 'computers': all_computers})


@admin_required
def edit_maintenance(request, id):
    record = get_object_or_404(Maintenance, id=id)
    if request.method == 'POST':
        record.computer_id = request.POST['computer']
        record.item = request.POST['item']
        record.quantity = request.POST['quantity']
        record.date = request.POST['date']
        record.cost = request.POST['cost']
        record.save()
        messages.success(request, 'Maintenance record has been updated successfully.')
        return redirect('maintenance')
    all_computers = Computer.objects.all()
    return render(request, 'edit_maintenance.html', {'record': record, 'computers': all_computers})


@admin_required
def delete_maintenance(request, id):
    record = get_object_or_404(Maintenance, id=id)
    if request.method == 'POST':
        record.delete()
        messages.success(request, 'Maintenance record has been deleted successfully.')
    return redirect('maintenance')


@login_required
def disposals(request):
    if request.method == 'POST':
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, 'Permission denied: View-only users cannot add disposals.')
            return redirect('disposals')
        Disposal.objects.create(
            computer_id=request.POST['computer'],
            date=request.POST['date'],
            reason=request.POST['reason'],
            method=request.POST['method'],
        )
        messages.success(request, 'Disposal record has been added successfully.')
        return redirect('disposals')
    all_disposals = Disposal.objects.all()
    all_computers = Computer.objects.all()
    return render(request, 'disposals.html', {'disposals': all_disposals, 'computers': all_computers})


@admin_required
def edit_disposal(request, id):
    disposal = get_object_or_404(Disposal, id=id)
    if request.method == 'POST':
        disposal.computer_id = request.POST['computer']
        disposal.date = request.POST['date']
        disposal.reason = request.POST['reason']
        disposal.method = request.POST['method']
        disposal.save()
        messages.success(request, 'Disposal record has been updated successfully.')
        return redirect('disposals')
    all_computers = Computer.objects.all()
    return render(request, 'edit_disposal.html', {'disposal': disposal, 'computers': all_computers})


@admin_required
def delete_disposal(request, id):
    disposal = get_object_or_404(Disposal, id=id)
    if request.method == 'POST':
        disposal.delete()
        messages.success(request, 'Disposal record has been deleted successfully.')
    return redirect('disposals')
