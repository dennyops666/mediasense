from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alerthistory',
            name='note',
            field=models.TextField(blank=True, null=True, verbose_name='备注'),
        ),
        migrations.AlterField(
            model_name='alerthistory',
            name='message',
            field=models.TextField(blank=True, null=True, default='', verbose_name='告警消息'),
        ),
    ] 