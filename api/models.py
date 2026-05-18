from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Region(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Viloyat'
        verbose_name_plural = 'Viloyatlar'
        ordering = ['name']


class District(models.Model):
    name = models.CharField(max_length=255)
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Tuman|Shahar'
        verbose_name_plural = 'Tuman|Shaharlar'
        ordering = ['name']


class Neighborhood(models.Model):
    name = models.CharField(max_length=255)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Mahalla'
        verbose_name_plural = 'Mahallalar'
        ordering = ['name']


class User(AbstractUser):
    ROLES = (
        ('worker', 'Worker'),
        ('supervisor', 'Inspektor'),
        ('admin', 'Admin'),
        ('owner', 'Buyurtmachi'),
        ('developer', 'Loyihachi'),
        ('builder', 'Quruvchi'),
        ('prokuratura', 'Prokuratura'),
        ('control', 'Nazorat'),
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
    profile = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.fullname

    class Meta:
        verbose_name_plural = 'Hodimlar'
        verbose_name = 'Hodim'


class ProjectOwnerCompany(models.Model):
    name = models.CharField(max_length=512, verbose_name=_("Tashkilot nomi"))
    description = models.TextField(verbose_name=_("Tashkilot haqida"), null=True, blank=True)
    inn = models.CharField(max_length=10, default='00000000')
    director = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='o_companies_as_director', verbose_name=_('Rahbari'))
    contact_person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='o_companies_as_contact', verbose_name=_("Ma'sul hodim"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    personal = models.ManyToManyField(Person, verbose_name=_('Hodimlar'))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Buyurtmachi tashkilotlar'
        verbose_name = 'Buyurtmachi tashkilot'


class ProjectDeveloperCompany(models.Model):
    name = models.CharField(max_length=512, verbose_name=_('Tashkilot nomi'))
    description = models.TextField(verbose_name=_('Tashkilot haqida'), null=True, blank=True)
    inn = models.CharField(max_length=10, default='00000000',)

    director = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='p_companies_as_director', verbose_name=_('Rahbari'))
    contact_person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='p_companies_as_contact', verbose_name=_("Ma'sul hodim"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    personal = models.ManyToManyField(Person, verbose_name=_('Hodimlar'))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Loyiha tashkilotlari'
        verbose_name = 'Loyiha tashkiloti'


class ConstructionCompany(models.Model):
    name = models.CharField(max_length=512, verbose_name=_('Tashkilot nomi'))
    description = models.TextField(verbose_name=_("Tashkilot haqida"), blank=True, null=True)
    inn = models.CharField(max_length=10, default='00000000')

    director = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='c_companies_as_director', verbose_name=_("Rahbari"))
    contact_person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='c_companies_as_contact', verbose_name=_("Ma'sul hodim"))

    personal = models.ManyToManyField(Person)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Qurilish tashkilotlari'
        verbose_name = 'Qurilish tashkiloti'


class GovermentProgram(models.Model):
    name = models.CharField(max_length=512, verbose_name=_('Qaror to\'liq nomi'))
    code = models.CharField(max_length=100, verbose_name=_('Qaror raqami'))
    description = models.TextField(verbose_name=_('Qisqacha ma\'lumot'), null=True, blank=True)
    budget = models.FloatField(verbose_name=_('Ajratilgan mablag\''), null=True, blank=True)

    def __str__(self):
        return self.code

    class Meta:
        verbose_name = 'Davlat dasturi'
        verbose_name_plural = 'Davlat dasturlari'
        ordering = ('name',)


class ConstructionObject(models.Model):
    realtime = True

    name = models.CharField(max_length=512, verbose_name=_('Nomi'))
    address = models.TextField(verbose_name=_('Manzil'))
    neighborhood = models.ForeignKey(Neighborhood, on_delete=models.SET_NULL, null=True, verbose_name=_('Mahalla'))
    latitude = models.FloatField()
    longitude = models.FloatField()
    deadline = models.DateField(null=True, blank=True, verbose_name=_('Qurilish topshirish muddati'), help_text=_("Topshirish muddatining oxirgi sanasi"))
    radius = models.FloatField(default=200, verbose_name=_('Qurilish radiusi'))
    building_count = models.PositiveSmallIntegerField(default=1, verbose_name=_('Obyektlar soni'))
    budget = models.FloatField(null=True, blank=True, verbose_name=_('Ajratilgan mablag\' (mln. so\'mda)'))
    contract_amount = models.FloatField(null=True, blank=True, verbose_name=_('Shartnoma qiymati (mln. so\'mda)'))
    workers = models.PositiveSmallIntegerField(default=1, verbose_name=_('Ishchilar'), help_text=_('Qurilishga jalb qilingan ishchilar soni'))
    machines =models.PositiveSmallIntegerField(default=0, verbose_name=_('Texnikalar'), help_text=_('Qurilishga jalb qilingan texnikalar soni'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    photo = models.ImageField(upload_to='objects/', blank=True, null=True, verbose_name=_('Loyiha rasmi'))
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_objects')
    developer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='developed_objects')
    owner_companies = models.ManyToManyField(ProjectOwnerCompany, verbose_name=_('Buyurtmachi tashkilotlar'))
    project_companies = models.ManyToManyField(ProjectDeveloperCompany, verbose_name=_('Loyihachi tashkilotlar'))
    construction_companies = models.ManyToManyField(ConstructionCompany, verbose_name=_('Qurilish tashkilotlari'))
    attached_person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name='attached_objects',
        verbose_name=_('Ma\'sul hodim'),
        null=True,
        blank=True,
    )
    is_government = models.BooleanField(default=False, verbose_name=_('Davlat qurilish obyekti?'))
    program = models.ForeignKey(GovermentProgram, on_delete=models.CASCADE, related_name='projects', verbose_name=_('Davlat dasturi'), null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Qurilish Loyihalari'
        verbose_name = 'Qurilish Loyihasi'
        ordering = ('name',)


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


class InspectionType(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Tekshiruv turlari'
        verbose_name = 'Tekshiruv turi'


class Review(models.Model):
    realtime = True
    class Status(models.TextChoices):
        PLANNED = 'planned', _('Rejalashtirilgan')
        IN_PROGRESS = 'in_progress', _('Jarayonda')
        COMPLETED = 'completed', _('Yakunlangan')
        CANCELLED = 'cancelled', _('Bekor qilingan')

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    object = models.ForeignKey(ConstructionObject, on_delete=models.CASCADE)
    planned_date = models.DateTimeField()
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reviews')
    inspection_types = models.ManyToManyField(InspectionType)
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
    realtime = True
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

class Status(models.TextChoices):
    OPEN = 'open', _('Ochiq')
    IN_PROGRESS = 'in_progress', _('Bartaraf etilmoqda')
    RESOLVED = 'resolved', _('Bartaraf etildi')

class IssueLevel(models.TextChoices):
    RED = 'red', _('Qizil')
    YELLOW = 'yellow', _('Sariq')
    GREEN = 'green', _('Yashil')

class Issue(models.Model):
    realtime = True

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


class LoginAttempt(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='login_attempts'
    )
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    successful = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} - {self.timestamp} - {'Success' if self.successful else 'Failed'}"


class IssueAction(models.Model):
    ISSUE_ACTION_TYPE = (
        ('resolved', 'Bartaraf etildi'),
        ('rejected', 'Rad etish'),
    )

    issue = models.ForeignKey(Issue, on_delete=models.CASCADE)
    action_type = models.CharField(choices=ISSUE_ACTION_TYPE, default='resolved', max_length=20, )
    report = models.TextField(max_length=3000)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='issue_actions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Kamchilik ustida amaliyotlar'
        verbose_name = 'Kamchilik ustida amaliyot'


class IssueActionPhoto(models.Model):
    issue_action = models.ForeignKey(IssueAction, on_delete=models.CASCADE)
    photo = models.ImageField(upload_to='report_photos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo for report {self.issue_action.id}"

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name_plural = 'Amaliyot fotolari'
        verbose_name = 'Amaliyot fotosi'


class ReviewComment(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, verbose_name='Tekshiruv')
    comment = models.TextField()
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='review_comments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Tekshiruv hisoboti izohlari'
        verbose_name = 'Tekshiruv hisoboti izohi'


class ReviewCommentPhoto(models.Model):
    review_comment = models.ForeignKey(ReviewComment, on_delete=models.CASCADE)
    photo = models.ImageField(upload_to='comment_photos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo for comment {self.review_comment.id}"

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name_plural = 'Amaliyot fotolari'
        verbose_name = 'Amaliyot fotosi'

class PublicIssue(models.Model):
    realtime = True

    issuer_fullname = models.CharField(max_length=255)
    issuer_phone = models.CharField(max_length=32)
    construction = models.ForeignKey(ConstructionObject, on_delete=models.CASCADE, null=True)
    title = models.CharField(max_length=512)
    description = models.CharField(max_length=512)
    issue_level = models.CharField(max_length=10, choices=IssueLevel.choices, default=IssueLevel.GREEN, )
    resolve_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Jamoatchilik qayd etgan muammolar'
        verbose_name = 'Jamoatchilik qayd etgan muammo'


class PublicIssuePhoto(models.Model):
    issue = models.ForeignKey(
        PublicIssue,
        on_delete=models.CASCADE,
        related_name='photos'
    )
    photo = models.ImageField(upload_to='public_issue_photos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo for issue {self.issue.id}"

    class Meta:
        verbose_name_plural = 'Foto'
        verbose_name = 'Foto'

class ConstructionFinancing(models.Model):
    construction = models.ForeignKey(ConstructionObject, on_delete=models.CASCADE, verbose_name=_('Qurilish loyihasi'))
    amount = models.PositiveBigIntegerField(default=0, verbose_name=_('Moliyalashtirilgan summa'))
    date = models.DateTimeField(default=timezone.now, verbose_name=_('Moliyalashtirilgan sana'))
    person = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Ma'sul shaxs"))
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.construction.name

    class Meta:
        verbose_name_plural = _('Moliyalashtirish tarixi')
        verbose_name = _('Moliyalashtirilgan summa')

class ConstructionDailyProgress(models.Model):
    construction = models.ForeignKey(ConstructionObject, on_delete=models.CASCADE)
    date = models.DateField(verbose_name=_('Sana'))
    amount = models.PositiveBigIntegerField(default=0, verbose_name=_('Ish hajmi'))
    workers = models.PositiveSmallIntegerField(default=0, verbose_name=_('Ishchilar soni'))
    machines = models.PositiveSmallIntegerField(default=0, verbose_name=_('Texnikalar soni'))

    class Meta:
        verbose_name = _('Qurilish kunlik')
        verbose_name_plural = _('Qurilish kunlik tarixi')

    def __str__(self):
        return self.construction.name

