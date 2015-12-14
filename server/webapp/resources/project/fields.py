from server.webapp.fields import Uuid, Json


project_copy_fields = {
    'project': Uuid,
    'user': Uuid,
    'copy_id': Uuid
}

predefined_fields = {
    "programs": Json,
    "populations": Json,
    "categories": Json
}
