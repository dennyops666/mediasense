from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0005_remove_systemmetrics_monitoring__metric__5bdd21_idx_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alertrule',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='是否启用'),
        ),
    ] 