# Generate a new uuid.
import uuid

def genuuid():
	# Generate a UUID
    return str(uuid.uuid4())

def shortuuid(uuid_str):
	# Return a short representation of the uuid_str
	return uuid_str[0:4]