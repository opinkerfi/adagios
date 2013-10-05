import django_tables


class HostTable(django_tables.MemoryTable):
    id = django_tables.Column(visible=False)
    host_name = django_tables.Column(verbose_name="Hostname")
    alias = django_tables.Column()
    register = django_tables.Column()
