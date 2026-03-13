from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0004_loan_emipayment'),
    ]

    operations = [
        migrations.AddField(
            model_name='emipayment',
            name='paid_amount',
            field=models.FloatField(default=0),
        ),
    ]
