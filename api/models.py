from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    ROLES = (
        ('worker', 'Worker'),
        ('supervisor', 'Supervisor'),
        ('admin', 'Admin'),
        ('author', 'Buyurtmachi'),
        ('developer', 'Loyihachi'),
        ('prokuratura', 'Prokuratura'),
    )

    role = models.CharField(max_length=20, choices=ROLES, default='worker')
    phone = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    objects = UserManager()

    class Meta:
        verbose_name_plural = 'Foydalanuvchilar'
        verbose_name = 'Foydalanuvchi'


class Person(models.Model):
    fullname = models.CharField(max_length=255)
    photo = models.ImageField(upload_to='photos/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    personal_phone = models.CharField(max_length=20, blank=True, null=True)
    profile = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.fullname

    class Meta:
        verbose_name_plural = 'Hodimlar'
        verbose_name = 'Hodim'


class ProjectDeveloperCompany(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    director = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='p_companies_as_director')
    contact_person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='p_companies_as_contact')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    personal = models.ManyToManyField(Person)


    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Loyiha tashkilotlari'
        verbose_name = 'Loyiha tashkiloti'


class ConstructionCompany(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()

    director = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='c_companies_as_director')
    contact_person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='c_companies_as_contact')

    personal = models.ManyToManyField(Person)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Qurilish tashkilotlari'
        verbose_name = 'Qurilish tashkiloti'


class ConstructionObject(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_objects')
    developer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='developed_objects')
    project_companies = models.ManyToManyField(ProjectDeveloperCompany)
    construction_companies = models.ManyToManyField(ConstructionCompany)
    is_government = models.BooleanField(default=False, verbose_name=_('Davlat qurilish obyekti?'))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Qurilish Loyihalari'
        verbose_name = 'Qurilish Loyihasi'


class ConstructionObjectDocumentType(models.Model):
    title = models.CharField(max_length=255)
    required = models.BooleanField(default=True, verbose_name=_('Majburiy?'))
    required_for_business = models.BooleanField(default=True, verbose_name=_('Xususiy sektor uchun majburiy?'))

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = 'Hujjat turlari'
        verbose_name = 'Hujjat turi'


class ConstructionObjectDocument(models.Model):
    construction = models.ForeignKey(ConstructionObject, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/', blank=True, null=True)
    document_type = models.ForeignKey(ConstructionObjectDocumentType, on_delete=models.CASCADE, null=False,
                                      verbose_name=_('Hujjat turi'), )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Hujjatlar'
        verbose_name = 'Hujjat'


class Review(models.Model):
    class Status(models.TextChoices):
        PLANNED = 'planned', _('Rejalashtirilgan')
        IN_PROGRESS = 'in_progress', _('Jarayonda')
        COMPLETED = 'completed', _('Yakunlangan')
        CANCELLED = 'cancelled', _('Bekor qilingan')

    name = models.CharField(max_length=255)
    description = models.TextField()
    object = models.ForeignKey(ConstructionObject, on_delete=models.CASCADE)
    planned_date = models.DateTimeField()
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reviews')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNED
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_reviews'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-planned_date']
        verbose_name_plural = 'Tekshiruvlar'
        verbose_name = 'Tekshiruv'

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class Report(models.Model):
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='reports'
    )
    comment = models.TextField()
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reports'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Tekshiruv Hisobotlari'
        verbose_name = 'Tekshiruv hisoboti'

    def __str__(self):
        return f"Report for {self.review.name} by {self.created_by}"


class ReportPhoto(models.Model):
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name='photos'
    )
    photo = models.ImageField(upload_to='report_photos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo for report {self.report.id}"

class IssueType(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Kamchilik turlari'
        verbose_name = 'Kamchilik turi'


class Issue(models.Model):
    class Status(models.TextChoices):
        OPEN = 'open', _('Ochiq')
        IN_PROGRESS = 'in_progress', _('Bartaraf etilmoqda')
        RESOLVED = 'resolved', _('Bartaraf etildi')

    class IssueLevel(models.TextChoices):
        RED = 'red', _('Qizil')
        YELLOW = 'yellow', _('Sariq')
        GREEN = 'green', _('Yashil')

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='issues'
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_issues'
    )
    issue_type = models.ForeignKey(IssueType, on_delete=models.SET_NULL, null=True)
    issue_level = models.CharField(max_length=10, choices=IssueLevel.choices, default=IssueLevel.GREEN, )
    resolve_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Aniqlangan kamchiliklar'
        verbose_name = 'Aniqlangan kamchilik'

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


class IssuePhoto(models.Model):
    issue = models.ForeignKey(
        Issue,
        on_delete=models.CASCADE,
        related_name='photos'
    )
    photo = models.ImageField(upload_to='issue_photos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo for issue {self.issue.id}"

    class Meta:
        verbose_name_plural = 'Foto'
        verbose_name = 'Foto'