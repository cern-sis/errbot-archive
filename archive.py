from itertools import chain

from errbot import BotPlugin, arg_botcmd

CONFIG_TEMPLATE = {
    "ARCHIVE_STREAM": "_archive",
}


class Archive(BotPlugin):
    def get_configuration_template(self):
        return CONFIG_TEMPLATE

    def configure(self, configuration):
        if configuration is not None and configuration != {}:
            config = dict(chain(CONFIG_TEMPLATE.items(), configuration.items()))
        else:
            config = CONFIG_TEMPLATE
            super(Archive, self).configure(config)

    @arg_botcmd(
        "-s",
        "--stream",
        type=str,
        help=""""
        The stream of the topic to archive.
        By default the stream in which the command is executed.
        """,
    )
    @arg_botcmd(
        "-t",
        "--topic",
        type=str,
        help="""
        The topic to archive.
        By default the topic in which the command is executed.
        """,
    )
    def archive(self, msg, stream=None, topic=None):
        """
        Archive a specific topic by moving it to ARCHIVE_STREAM.
        """
        if stream is None:
            stream = self.current_stream(msg)
        if topic is None:
            topic = self.current_topic(msg)
        self.archive_topic(stream, topic)

    @arg_botcmd(
        "-t",
        "--topic",
        type=str,
        help="""
        The topic to restore.
        By default the topic in which the command is executed.
        """,
    )
    def restore(self, msg, topic=None):
        """
        Restore a specific topic from the ARCHIVE_STREAM.
        """
        if topic is None:
            topic = self.current_topic(msg)
        self.restore_topic(topic)

    def zulip_client(self):
        return self._bot.client

    @staticmethod
    def current_stream(msg):
        return msg._from._room._id

    @staticmethod
    def current_topic(msg):
        return msg._from._room._subject

    def archive_topic(self, stream, topic):
        msg = self.get_last_message(stream, topic)
        self.move_topic(
            msg["id"],
            self.config["ARCHIVE_STREAM"],
            self.archived_topic(stream, topic),
        )

    def archived_topic(self, stream, topic):
        return f"✔ {stream}/{topic.replace('✔ ', '')}"

    def get_last_message(self, stream, topic):
        client = self.zulip_client()
        request = {
            "anchor": "newest",
            "include_anchor": True,
            "num_before": 1,
            "num_after": 0,
            "narrow": [
                {"operator": "stream", "operand": stream},
                {"operator": "topic", "operand": topic},
            ],
        }
        response = client.get_messages(request)
        return response["messages"][0]

    def move_topic(self, msg_id, stream, topic):
        client = self.zulip_client()
        response = client.get_stream_id(stream)
        stream_id = response["stream_id"]
        request = {
            "message_id": msg_id,
            "propagate_mode": "change_all",
            "send_notification_to_new_thread": False,
            "stream_id": stream_id,
            "topic": topic,
        }
        client.update_message(request)

    def restore_topic(self, topic):
        msg = self.get_last_message(self.config["ARCHIVE_STREAM"], topic)
        new_stream, new_topic = topic.replace("✔ ", "").split("/", 1)
        self.move_topic(msg["id"], new_stream, new_topic)
