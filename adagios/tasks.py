
import adagios.settings
from celery import Celery, current_task
from okconfig.helper_functions import clientInstall
import time


def initialize():
    """
    Initialize connection parameters to the celery backend/broker
    """
    c = Celery('adagios.tasks',
               backend=adagios.settings.celery_backend,
               broker=adagios.settings.celery_broker,
               dburi=adagios.settings.celery_result_dburi)
    c.conf['CELERY_RESULT_DBURI'] = adagios.settings.celery_result_dburi
    return c

# Initialize connection parameters
celery = initialize()

@celery.task("adagios.tasks.okconfig_installClient", ignore_result=False)
def okconfig_installNSClient(host_name, domain, username, password):
    """
    Starts clientInstall asynchronously and updates the tasks state every
    second. Returns the state when done.
    """
    c = clientInstall(script_args=[host_name], merge_env={
        "DOMAIN": domain,
        "DOMAIN_USER": username,
        "DOMAIN_PASSWORD": password })
    c.execute()

    while True:
        current_state, progress = c.get_state()
        current_task.update_state(state='RUNNING', meta=(current_state, progress))

        # Script has ended
        if c.process.poll() is not None:
            c.get_state()
            current_task.update_state(state='DONE', meta=(current_state, progress))
            break
        time.sleep(1)
    return c.get_state()
