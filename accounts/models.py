from django.contrib.auth.models import AbstractUser
from django.db import models


class Foydalanuvchi(AbstractUser):
    """Sayt foydalanuvchisi.

    DIQQAT: Bu model Django admin (/boshqaruv/) uchun ham, sayt paneli uchun ham
    ishlatiladi, lekin kirish huquqlari ALOHIDA:
      * Django admin  -> faqat is_superuser=True bo'lgan hisoblar kira oladi.
      * Sayt paneli   -> rol = admin yoki operator bo'lgan faol hisoblar.
    Ya'ni sayt admini Django admin paroli bilan bir xil bo'lishi shart emas.
    """

    class Rol(models.TextChoices):
        ADMIN = "admin", "Sayt admini"
        OPERATOR = "operator", "Operator"

    rol = models.CharField("Rol", max_length=20, choices=Rol.choices, default=Rol.OPERATOR)
    telefon = models.CharField("Telefon", max_length=30, blank=True)
    saytga_kira_oladi = models.BooleanField(
        "Sayt paneliga kira oladi", default=True,
        help_text="O'chirilsa, bu hisob sayt paneliga kira olmaydi.",
    )

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"
        ordering = ["username"]

    def __str__(self):
        return self.toliq_ism

    @property
    def toliq_ism(self):
        """O'zbekcha tartibda: Familiya Ism."""
        toliq = f"{self.last_name} {self.first_name}".strip()
        return toliq or self.username

    @property
    def admin_mi(self):
        """Sayt admini (to'liq huquq) yoki superuser."""
        return self.rol == self.Rol.ADMIN or self.is_superuser
