from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0005_emipayment_paid_amount'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emipayment',
            name='status',
            field=models.CharField(
                choices=[('pending', 'Pending'), ('partial', 'Partial'), ('paid', 'Paid')],
                default='pending',
                max_length=10,
            ),
        ),
    ]
