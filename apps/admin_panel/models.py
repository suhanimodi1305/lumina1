"""
Admin Panel extra models:
  - AdminActivity (audit log for every admin action)
  - CompanySettings (SMTP, branding, etc.)
  - SalaryRecord, EmployeeLeave, EmployeeDocument, Department
  - AdminNotification, AdminTask
"""
from django.db import models
from django.contrib.auth.models import User
import uuid


# ─────────────────────────────────────────────────────────────────────────────
# DEPARTMENT
# ─────────────────────────────────────────────────────────────────────────────

class Department(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    code        = models.CharField(max_length=20, unique=True, blank=True)
    head        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='headed_departments')
    description = models.TextField(blank=True)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Department'

    def __str__(self):
        return self.name


# ─────────────────────────────────────────────────────────────────────────────
# EMPLOYEE PROFILE EXTENSION
# ─────────────────────────────────────────────────────────────────────────────

class EmployeeProfile(models.Model):
    BLOOD_GROUP_CHOICES = [
        ('A+','A+'),('A-','A-'),('B+','B+'),('B-','B-'),
        ('AB+','AB+'),('AB-','AB-'),('O+','O+'),('O-','O-'),
    ]
    GENDER_CHOICES = [
        ('male','Male'),('female','Female'),('other','Other'),
    ]
    STATUS_CHOICES = [
        ('active','Active'),('inactive','Inactive'),('terminated','Terminated'),('on_leave','On Leave'),
    ]
    SHIFT_CHOICES = [
        ('morning','Morning (9AM-6PM)'),('afternoon','Afternoon (2PM-11PM)'),
        ('night','Night (10PM-7AM)'),('flexible','Flexible'),
    ]

    user            = models.OneToOneField(User, on_delete=models.CASCADE, related_name='emp_profile')
    employee_id     = models.CharField(max_length=20, unique=True, blank=True)
    department      = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='members')
    designation     = models.CharField(max_length=100, blank=True)
    joining_date    = models.DateField(null=True, blank=True)
    status          = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')

    # Personal
    phone           = models.CharField(max_length=15, blank=True)
    emergency_contact = models.CharField(max_length=15, blank=True)
    emergency_name  = models.CharField(max_length=100, blank=True)
    dob             = models.DateField(null=True, blank=True)
    gender          = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    blood_group     = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES, blank=True)

    # Address
    address         = models.TextField(blank=True)
    city            = models.CharField(max_length=80, blank=True)
    state           = models.CharField(max_length=80, blank=True)
    country         = models.CharField(max_length=80, default='India')
    pincode         = models.CharField(max_length=10, blank=True)

    # Professional
    experience_years = models.PositiveSmallIntegerField(default=0)
    qualification   = models.CharField(max_length=200, blank=True)
    college         = models.CharField(max_length=200, blank=True)
    university      = models.CharField(max_length=200, blank=True)
    skills          = models.TextField(blank=True, help_text='Comma-separated')
    languages       = models.CharField(max_length=200, blank=True)
    previous_company = models.CharField(max_length=200, blank=True)

    # Shift
    shift           = models.CharField(max_length=15, choices=SHIFT_CHOICES, default='morning')

    # Bank
    bank_name       = models.CharField(max_length=100, blank=True)
    account_number  = models.CharField(max_length=30, blank=True)
    ifsc_code       = models.CharField(max_length=15, blank=True)
    pan_number      = models.CharField(max_length=15, blank=True)

    # Photo
    photo           = models.ImageField(upload_to='employees/%Y/', null=True, blank=True)

    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Employee Profile'

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} [{self.employee_id or 'N/A'}]"

    def save(self, *args, **kwargs):
        if not self.employee_id:
            from django.utils import timezone
            import secrets
            now = timezone.now()
            suffix = secrets.token_hex(2).upper()
            self.employee_id = f"EMP{now.strftime('%y%m%d')}{suffix}"
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# EMPLOYEE DOCUMENT
# ─────────────────────────────────────────────────────────────────────────────

class EmployeeDocument(models.Model):
    DOC_TYPE_CHOICES = [
        ('aadhaar',         'Aadhaar Card'),
        ('pan',             'PAN Card'),
        ('passport',        'Passport'),
        ('driving_license', 'Driving License'),
        ('voter_id',        'Voter ID'),
        ('resume',          'Resume'),
        ('offer_letter',    'Offer Letter'),
        ('appointment_letter','Appointment Letter'),
        ('education_cert',  'Education Certificate'),
        ('degree',          'Degree'),
        ('class10',         '10th Marksheet'),
        ('class12',         '12th Marksheet'),
        ('bachelor',        'Bachelor\'s Degree'),
        ('master',          'Master\'s Degree'),
        ('experience_letter','Experience Letter'),
        ('salary_slip',     'Salary Slip'),
        ('bank_passbook',   'Bank Passbook'),
        ('cancelled_cheque','Cancelled Cheque'),
        ('passport_photo',  'Passport Photo'),
        ('signature',       'Signature'),
        ('police_verification','Police Verification'),
        ('medical_cert',    'Medical Certificate'),
        ('other',           'Other'),
    ]
    STATUS_CHOICES = [
        ('pending',  'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]

    employee    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emp_documents')
    doc_type    = models.CharField(max_length=30, choices=DOC_TYPE_CHOICES)
    document    = models.FileField(upload_to='emp_docs/%Y/')
    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    notes       = models.CharField(max_length=300, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='verified_docs')

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Employee Document'

    def __str__(self):
        return f"{self.employee.username} — {self.get_doc_type_display()}"


# ─────────────────────────────────────────────────────────────────────────────
# SALARY RECORD
# ─────────────────────────────────────────────────────────────────────────────

class SalaryRecord(models.Model):
    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('processed', 'Processed'),
        ('paid',      'Paid'),
        ('on_hold',   'On Hold'),
    ]

    employee        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='salary_records')
    month           = models.PositiveSmallIntegerField()   # 1-12
    year            = models.PositiveSmallIntegerField()
    basic_salary    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hra             = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    allowances      = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    incentives      = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions      = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_deducted    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_salary      = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status          = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    payment_date    = models.DateField(null=True, blank=True)
    payment_ref     = models.CharField(max_length=100, blank=True)
    notes           = models.TextField(blank=True)
    created_by      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='created_salaries')
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('employee', 'month', 'year')
        ordering = ['-year', '-month']
        verbose_name = 'Salary Record'

    def __str__(self):
        return f"{self.employee.username} — {self.month}/{self.year} [₹{self.net_salary}]"

    def compute_net(self):
        gross = self.basic_salary + self.hra + self.allowances + self.incentives
        self.net_salary = gross - self.deductions - self.tax_deducted
        return self.net_salary


# ─────────────────────────────────────────────────────────────────────────────
# EMPLOYEE LEAVE
# ─────────────────────────────────────────────────────────────────────────────

class EmployeeLeave(models.Model):
    LEAVE_TYPE_CHOICES = [
        ('casual',    'Casual Leave'),
        ('sick',      'Sick Leave'),
        ('earned',    'Earned Leave'),
        ('maternity', 'Maternity Leave'),
        ('paternity', 'Paternity Leave'),
        ('unpaid',    'Unpaid Leave'),
        ('comp_off',  'Compensatory Off'),
    ]
    STATUS_CHOICES = [
        ('pending',  'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled','Cancelled'),
    ]

    employee    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type  = models.CharField(max_length=15, choices=LEAVE_TYPE_CHOICES, default='casual')
    from_date   = models.DateField()
    to_date     = models.DateField()
    days        = models.PositiveSmallIntegerField(default=1)
    reason      = models.TextField()
    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='approved_leaves')
    admin_notes = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Employee Leave'

    def __str__(self):
        return f"{self.employee.username} — {self.leave_type} {self.from_date}→{self.to_date}"


# ─────────────────────────────────────────────────────────────────────────────
# COMPANY SETTINGS
# ─────────────────────────────────────────────────────────────────────────────

class CompanySettings(models.Model):
    # Singleton — only one row allowed
    company_name    = models.CharField(max_length=200, default='Lumina AI')
    company_email   = models.EmailField(default='suhanimodi7090@gmail.com')
    support_email   = models.EmailField(default='suhanimodi7090@gmail.com')
    hr_email        = models.EmailField(default='suhanimodi7090@gmail.com')
    sales_email     = models.EmailField(default='suhanimodi7090@gmail.com')
    marketing_email = models.EmailField(default='suhanimodi7090@gmail.com')
    phone           = models.CharField(max_length=20, blank=True)
    address         = models.TextField(blank=True)
    city            = models.CharField(max_length=80, blank=True)
    state           = models.CharField(max_length=80, blank=True)
    pincode         = models.CharField(max_length=10, blank=True)
    gstin           = models.CharField(max_length=20, blank=True)
    website         = models.URLField(blank=True)
    currency        = models.CharField(max_length=5, default='INR')
    timezone        = models.CharField(max_length=50, default='Asia/Kolkata')
    smtp_host       = models.CharField(max_length=100, default='smtp.gmail.com')
    smtp_port       = models.PositiveSmallIntegerField(default=587)
    smtp_user       = models.EmailField(default='suhanimodi7090@gmail.com')
    logo            = models.ImageField(upload_to='company/', null=True, blank=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Company Settings'

    def __str__(self):
        return self.company_name


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN ACTIVITY LOG (immutable audit trail)
# ─────────────────────────────────────────────────────────────────────────────

class AdminActivity(models.Model):
    ACTION_CHOICES = [
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
        ('login',  'Login'),
        ('logout', 'Logout'),
        ('export', 'Exported'),
        ('import', 'Imported'),
        ('approve','Approved'),
        ('reject', 'Rejected'),
        ('other',  'Other'),
    ]

    admin       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                    related_name='admin_activities')
    action      = models.CharField(max_length=10, choices=ACTION_CHOICES)
    module      = models.CharField(max_length=50)          # 'employees', 'orders', etc.
    description = models.TextField()
    ip_address  = models.GenericIPAddressField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Admin Activity'
        verbose_name_plural = 'Admin Activities'

    def __str__(self):
        admin = self.admin.username if self.admin else 'system'
        return f"{admin} — {self.action} {self.module} at {self.created_at:%d %b %H:%M}"


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN TASK
# ─────────────────────────────────────────────────────────────────────────────

class AdminTask(models.Model):
    PRIORITY_CHOICES = [
        ('low',    'Low'),
        ('medium', 'Medium'),
        ('high',   'High'),
        ('urgent', 'Urgent'),
    ]
    STATUS_CHOICES = [
        ('todo',       'To Do'),
        ('in_progress','In Progress'),
        ('done',       'Done'),
        ('cancelled',  'Cancelled'),
    ]

    title       = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='admin_tasks')
    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='tasks_created')
    priority    = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status      = models.CharField(max_length=15, choices=STATUS_CHOICES, default='todo')
    due_date    = models.DateField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Admin Task'

    def __str__(self):
        return f"[{self.priority.upper()}] {self.title[:60]}"
