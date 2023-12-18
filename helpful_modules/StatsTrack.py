import dataclasses
import io

try:
    import orjson as json
except ImportError:
    import json


@dataclasses.dataclass
class CommandUsage:
    user_id: int
    command_name: str
    time: float

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "command_name": self.command_name,
            "time": self.time,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


class CommandStats:
    usages: [CommandUsage]
    unique_users: set[int]
    total_cmds_used: int

    def __init__(self, usages, total_cmds, unique_users):
        self.usages = usages
        self.total_cmds = total_cmds
        self.unique_users = set(unique_users)

    def update_with_new_usage(self, usage: CommandUsage):
        self.usages.append(usage)
        self.unique_users.add(usage.user_id)
        self.total_cmds += 1

    @property
    def num_unique_users(self):
        # this could be more efficient by adding more properties
        return len(self.unique_users)

    def to_dict(self):
        return {
            "usages": [usage.to_dict for usage in self.usages],
            "unique_users": list(self.unique_users),
            "total_cmds": self.total_cmds,
        }

    def represent(self):
        # represent self as a string
        return str(self.to_dict())

    def __str__(self):
        return self.represent()

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


class StreamWrapperStorer:
    stream: [io.StringIO]
    reading: [io.StringIO]  # must have a readline() function

    def __init__(self, stream, reading):
        self.stream = stream
        self.reading = reading

    def writeStats(self, stats: CommandStats):
        self.stream.write(str(stats))

    def return_stats(self):
        # assume the stats object is in ONE LINE (not multiple)
        return json.loads(self.reading.readline())

    def close(self):
        self.stream.close()
