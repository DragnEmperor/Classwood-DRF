from django.db import models
from django.db.models import UniqueConstraint


class FeesDetails(models.Model):
    """Fee structure for a classroom."""

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    due_date = models.DateField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    for_class = models.ForeignKey("ClassroomModel", on_delete=models.CASCADE)
    session = models.ForeignKey("SessionModel", on_delete=models.CASCADE)
    fee_type = models.TextField()
    school = models.ForeignKey("SchoolModel", on_delete=models.CASCADE)

    class Meta:
        ordering = ["-due_date"]

    def __str__(self):
        return f"{self.fee_type} - {self.amount}"


class PaymentInfo(models.Model):
    """Record of a fee payment by a student."""

    PAYMENT_MODE_CHOICES = [
        ("1", "Cheque"),
        ("2", "Cash at Counter"),
        ("3", "Net Banking"),
        ("4", "Demand Draft"),
    ]

    student = models.ForeignKey("StudentModel", on_delete=models.CASCADE)
    fees = models.ForeignKey(FeesDetails, on_delete=models.CASCADE)
    payment_mode = models.CharField(max_length=1, choices=PAYMENT_MODE_CHOICES)
    payment_date = models.DateField()
    reference = models.CharField(max_length=50, blank=True, null=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        constraints = [
            UniqueConstraint(fields=["student", "fees"], name="unique_payment_per_student_fees"),
        ]
        ordering = ["-payment_date"]
        verbose_name = "Payment"
        verbose_name_plural = "Payments"

    def __str__(self):
        return f"{self.student} - {self.fees}"
