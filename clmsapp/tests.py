from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Lab, Computer, Specification, Instructor, Schedule, Attendant, Maintenance, Disposal


class UserDashboardAndPermissionsTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Admin user (staff/superuser)
        self.admin_user = User.objects.create_user(
            username='admin_test',
            password='Password123!',
            is_staff=True,
            is_superuser=True
        )

        # Standard regular user (non-staff)
        self.regular_user = User.objects.create_user(
            username='viewer_test',
            password='Password123!',
            is_staff=False,
            is_superuser=False
        )

        # Dummy data
        self.lab = Lab.objects.create(name='Test Lab 1', location='Main Campus', capacity=30, duration=2)
        self.computer = Computer.objects.create(
            name='PC-TEST-01', brand='Dell', type='Desktop', colour='Black', lab=self.lab, status='Active'
        )
        self.spec = Specification.objects.create(
            computer=self.computer, processor='Intel Core i7', ram=16, storage=512, operating_system='Windows 11'
        )
        self.instructor = Instructor.objects.create(
            full_name='Dr. Test', phone='0700000000', email='test@iuiu.ac.ug', department='IT'
        )
        self.schedule = Schedule.objects.create(
            lab=self.lab, day='MON', start_time='09:00:00', end_time='11:00:00', instructor=self.instructor
        )
        self.attendant = Attendant.objects.create(
            full_name='Attendant Test', phone='0711111111', lab=self.lab, shift='Day'
        )
        self.maintenance = Maintenance.objects.create(
            computer=self.computer, item='RAM upgrade', quantity=1, date='2026-11-10', cost=50000
        )
        self.disposal = Disposal.objects.create(
            computer=self.computer, date='2026-11-10', reason='Damaged', method='Scrapped'
        )

    def test_unauthenticated_user_redirected_to_login(self):
        response = self.client.get(reverse('user_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_regular_user_login_redirects_to_user_dashboard(self):
        response = self.client.post(reverse('login'), {
            'username': 'viewer_test',
            'password': 'Password123!'
        })
        self.assertRedirects(response, reverse('user_dashboard'))

    def test_admin_user_login_redirects_to_admin_index(self):
        response = self.client.post(reverse('login'), {
            'username': 'admin_test',
            'password': 'Password123!'
        })
        self.assertRedirects(response, reverse('index'))

    def test_regular_user_accessing_index_redirects_to_user_dashboard(self):
        self.client.login(username='viewer_test', password='Password123!')
        response = self.client.get(reverse('index'))
        self.assertRedirects(response, reverse('user_dashboard'))

    def test_user_dashboard_view_contains_expected_data_and_no_actions(self):
        self.client.login(username='viewer_test', password='Password123!')
        response = self.client.get(reverse('user_dashboard'))
        self.assertEqual(response.status_code, 200)

        # Check content present
        content = response.content.decode('utf-8')
        self.assertIn('Computer Lab Viewer Portal', content)
        self.assertIn('Read-Only Mode', content)
        self.assertIn('Test Lab 1', content)
        self.assertIn('PC-TEST-01', content)
        self.assertIn('Intel Core i7', content)
        self.assertIn('Dr. Test', content)
        self.assertIn('Attendant Test', content)

        # Ensure NO edit / delete buttons or forms are in the user dashboard
        self.assertNotIn('class="icon-btn icon-edit"', content)
        self.assertNotIn('class="icon-btn icon-delete"', content)
        self.assertNotIn('Add New Lab', content)
        self.assertNotIn('Add New Computer', content)

    def test_regular_user_cannot_create_or_modify_or_delete_lab(self):
        self.client.login(username='viewer_test', password='Password123!')
        # Create blocked
        initial_count = Lab.objects.count()
        response = self.client.post(reverse('labs'), {
            'name': 'Unauthorized Lab', 'location': 'Secret', 'capacity': 10, 'duration': 1,
        })
        self.assertRedirects(response, reverse('labs'))
        self.assertEqual(Lab.objects.count(), initial_count)

        # Edit blocked
        res_edit = self.client.post(reverse('edit_lab', args=[self.lab.id]), {
            'name': 'Hacked Lab', 'location': 'Hacked', 'capacity': 99, 'duration': 99,
        })
        self.assertRedirects(res_edit, reverse('user_dashboard'))
        self.lab.refresh_from_db()
        self.assertEqual(self.lab.name, 'Test Lab 1')

        # Delete blocked
        res_del = self.client.post(reverse('delete_lab', args=[self.lab.id]))
        self.assertRedirects(res_del, reverse('user_dashboard'))
        self.assertTrue(Lab.objects.filter(id=self.lab.id).exists())

    def test_regular_user_cannot_create_or_modify_or_delete_computer(self):
        self.client.login(username='viewer_test', password='Password123!')
        comp_count = Computer.objects.count()
        response = self.client.post(reverse('computers'), {
            'name': 'PC-HACK', 'brand': 'None', 'type': 'Desktop', 'colour': 'Red', 'lab': self.lab.id, 'status': 'Active'
        })
        self.assertRedirects(response, reverse('computers'))
        self.assertEqual(Computer.objects.count(), comp_count)

        res_edit = self.client.post(reverse('edit_computer', args=[self.computer.id]), {
            'name': 'PC-MODIFIED', 'brand': 'None', 'type': 'Desktop', 'colour': 'Red', 'lab': self.lab.id, 'status': 'Active'
        })
        self.assertRedirects(res_edit, reverse('user_dashboard'))
        self.computer.refresh_from_db()
        self.assertEqual(self.computer.name, 'PC-TEST-01')

        res_del = self.client.post(reverse('delete_computer', args=[self.computer.id]))
        self.assertRedirects(res_del, reverse('user_dashboard'))
        self.assertTrue(Computer.objects.filter(id=self.computer.id).exists())

    def test_regular_user_cannot_create_or_modify_or_delete_schedule(self):
        self.client.login(username='viewer_test', password='Password123!')
        sched_count = Schedule.objects.count()
        response = self.client.post(reverse('schedules'), {
            'lab': self.lab.id, 'day': 'TUE', 'start_time': '10:00', 'end_time': '12:00', 'instructor': self.instructor.id
        })
        self.assertRedirects(response, reverse('schedules'))
        self.assertEqual(Schedule.objects.count(), sched_count)

        res_del = self.client.post(reverse('delete_schedule', args=[self.schedule.id]))
        self.assertRedirects(res_del, reverse('user_dashboard'))
        self.assertTrue(Schedule.objects.filter(id=self.schedule.id).exists())

    def test_regular_user_cannot_create_or_modify_or_delete_attendant(self):
        self.client.login(username='viewer_test', password='Password123!')
        att_count = Attendant.objects.count()
        response = self.client.post(reverse('attendants'), {
            'full_name': 'Attendant 2', 'phone': '0722222222', 'lab': self.lab.id, 'shift': 'Evening'
        })
        self.assertRedirects(response, reverse('attendants'))
        self.assertEqual(Attendant.objects.count(), att_count)

        res_del = self.client.post(reverse('delete_attendant', args=[self.attendant.id]))
        self.assertRedirects(res_del, reverse('user_dashboard'))
        self.assertTrue(Attendant.objects.filter(id=self.attendant.id).exists())

    def test_regular_user_cannot_create_or_modify_or_delete_maintenance(self):
        self.client.login(username='viewer_test', password='Password123!')
        maint_count = Maintenance.objects.count()
        response = self.client.post(reverse('maintenance'), {
            'computer': self.computer.id, 'item': 'Power cable', 'quantity': 1, 'date': '2026-11-12', 'cost': 10000
        })
        self.assertRedirects(response, reverse('maintenance'))
        self.assertEqual(Maintenance.objects.count(), maint_count)

        res_del = self.client.post(reverse('delete_maintenance', args=[self.maintenance.id]))
        self.assertRedirects(res_del, reverse('user_dashboard'))
        self.assertTrue(Maintenance.objects.filter(id=self.maintenance.id).exists())

    def test_regular_user_cannot_create_or_modify_or_delete_disposal(self):
        self.client.login(username='viewer_test', password='Password123!')
        disp_count = Disposal.objects.count()
        response = self.client.post(reverse('disposals'), {
            'computer': self.computer.id, 'date': '2026-11-12', 'reason': 'Obsolete', 'method': 'Recycled'
        })
        self.assertRedirects(response, reverse('disposals'))
        self.assertEqual(Disposal.objects.count(), disp_count)

        res_del = self.client.post(reverse('delete_disposal', args=[self.disposal.id]))
        self.assertRedirects(res_del, reverse('user_dashboard'))
        self.assertTrue(Disposal.objects.filter(id=self.disposal.id).exists())

    def test_admin_can_perform_crud(self):
        self.client.login(username='admin_test', password='Password123!')
        response = self.client.post(reverse('edit_lab', args=[self.lab.id]), {
            'name': 'Updated Lab Name',
            'location': 'Updated Location',
            'capacity': 45,
            'duration': 3,
        })
        self.assertRedirects(response, reverse('labs'))
        self.lab.refresh_from_db()
        self.assertEqual(self.lab.name, 'Updated Lab Name')
