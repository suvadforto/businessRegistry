from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


from django.db import models

from django.utils import timezone

class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save()


class ActivityCode(models.Model):
    code = models.CharField(max_length=10, unique=True)
    description = models.CharField(max_length=255)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} – {self.description}"
        
class Business(SoftDeleteModel):
    STATUS_CHOICES = [
        ('active', 'Aktivan'),
        ('inactive', 'Neaktivan'),
        ('suspended', 'Na čekanju'),
    ]
    BUSINESS_TYPE_CHOICES = [
    ('osnovno', 'Osnovno'),
    ('dopunsko', 'Dopunsko'),
    ('dodatno', 'Dodatno'),
    ]
    business_type = models.CharField(
    max_length=20,
    choices=BUSINESS_TYPE_CHOICES,
    default='osnovno',
    verbose_name="Način obavljanja"
)
#New fields 12.02.2026
    start_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Datum početka rada"
    )

    end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Datum prestanka rada"
    )

    number_of_employees = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Broj zaposlenih"
    )
    is_vat_registered = models.BooleanField(
        default=False,
        verbose_name="PDV obveznik"
    )

    bank_account = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Broj računa"
    )
    activity_code = models.ForeignKey(
    ActivityCode,
    on_delete=models.SET_NULL,
    null=True,
    related_name='primary_businesses',
    verbose_name="Glavna djelatnost"
    )

    secondary_activities = models.ManyToManyField(
    ActivityCode,
    blank=True,
    related_name='secondary_businesses',
    verbose_name="Dodatne djelatnosti"
    )
    internal_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Interne napomene"
    )
    assigned_clerk = models.ForeignKey(
            "User",
            on_delete=models.SET_NULL,
            blank=True,
            null=True,
            limit_choices_to={'role': 'clerk'},
            related_name='assigned_businesses',
            verbose_name="Dodijeljeni službenik"
    )

    
#END OF NEW FIELDS 
                
    name = models.CharField(max_length=255,verbose_name="Naziv obrta")
    registration_number = models.CharField(max_length=100, unique=True, verbose_name="Broj rješenja")
    tax_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Porezni id br.")
    industry = models.CharField(max_length=150, blank=True, null=True,verbose_name="Vrsta obrta")
    legal_form = models.CharField(max_length=100, blank=True, null=True, verbose_name="Zanimanje")

    address = models.TextField(blank=True, null=True, verbose_name="Adresa/Sjedište")
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name="Grad")
    postal_code = models.CharField(max_length=20, blank=True, null=True, verbose_name="Poštanski broj")

    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="Telefon")
    email = models.EmailField(blank=True, null=True)

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='active'
    )

    date_registered = models.DateField(verbose_name="Datum registracije")
    notes = models.TextField(blank=True, null=True, verbose_name="Zabilješke")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = ActiveManager()
    all_objects = models.Manager()
    
    def clean(self):
        super().clean()
        errors = {}
        
            
        if self.end_date and self.start_date:
            if self.end_date < self.start_date:
                errors['end_date'] = "Datum prestanka rada ne može biti prije datuma početka rada."

        if self.assigned_clerk and self.assigned_clerk.role != 'clerk':
            errors['assigned_clerk'] = "Dodijeljeni korisnik mora biti službenik (clerk)."

        if errors:
            raise ValidationError(errors)
    
    
            
    class Meta:
        verbose_name = _("Obrt")
        verbose_name_plural = _("Obrti")
        
    def __str__(self):
        return f"{self.name} ({self.registration_number})"
        


class Owner(SoftDeleteModel):
    first_name = models.CharField(max_length=100, verbose_name="Ime Vlasnika")
    last_name = models.CharField(max_length=100, verbose_name="Prezime Vlasnika")
    personal_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="JMBG")

    address = models.TextField(blank=True, null=True, verbose_name="Adresa")
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="Telefon")
    email = models.EmailField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Datum i vrijeme unosa")
    
    objects = ActiveManager()
    all_objects = models.Manager()
    
    class Meta:
        verbose_name = "Vlasnik"
        verbose_name_plural = "Vlasnici"
        
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

#BusinessOwner (Many-to-Many with extra fields)
class BusinessOwner(models.Model):
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='ownerships'
    )
    owner = models.ForeignKey(
        Owner,
        on_delete=models.CASCADE,
        related_name='businesses'
    )
    ownership_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True
    )

    class Meta:
        unique_together = ('business', 'owner')
        verbose_name = "Vlasnik"
        verbose_name_plural = "Vlasnici"

    def __str__(self):
        return f"{self.owner} → {self.business}"

class License(SoftDeleteModel):
    STATUS_CHOICES = [
        ('valid', 'Valid'),
        ('expired', 'Expired'),
        ('revoked', 'Revoked'),
    ]

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='licenses'
    )

    license_type = models.CharField(max_length=150)
    license_number = models.CharField(max_length=100)
    issue_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES
    )
    
    objects = ActiveManager()
    all_objects = models.Manager()

    notes = models.TextField(blank=True, null=True)
    class Meta:
        verbose_name = "Dozvola"
        verbose_name_plural = "Dozvole"
        
    def __str__(self):
        return f"{self.license_type} – {self.business.name}"


class Inspection(models.Model):
    RESULT_CHOICES = [
        ('passed', 'Passed'),
        ('failed', 'Failed'),
    ]

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='inspections'
    )

    inspection_date = models.DateField()
    inspector_name = models.CharField(max_length=150)
    result = models.CharField(max_length=50, choices=RESULT_CHOICES)
    remarks = models.TextField(blank=True, null=True)
    class Meta:
        verbose_name = "Inspekcija"
        verbose_name_plural = "Inspekcije"
    def __str__(self):
        return f"{self.business.name} – {self.inspection_date}"

class Document(models.Model):
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='documents'
    )

    document_type = models.CharField(max_length=100)
    file = models.FileField(upload_to='documents/%Y/%m/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = "Dokument"
        verbose_name_plural = "Dokumenti"
    def __str__(self):
        return f"{self.document_type} – {self.business.name}"

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('clerk', 'Clerk'),
        ('viewer', 'Viewer'),
    ]

    role = models.CharField(
        max_length=50,
        choices=ROLE_CHOICES,
        default='viewer'
    )

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES
    )

    table_name = models.CharField(max_length=100)
    record_id = models.PositiveIntegerField()
    action_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} – {self.table_name} ({self.record_id})"

    class Meta:
        indexes = [
            models.Index(fields=['table_name', 'record_id']),
            models.Index(fields=['action_time']),
        ]



# Create your models here.
