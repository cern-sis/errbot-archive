from errbot import BotPlugin, arg_botcmd


class Archive(BotPlugin):
    @staticmethod
    def get_configuration_template():
        return {
            "ARCHIVE_STREAM": "_archive",
        }

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

    @staticmethod
    def current_stream(msg):
        return msg._from._room._id

    @staticmethod
    def current_topic(msg):
        return msg._from._room._subject

    def archive_topic(self, stream, topic):
        msg = self.get_last_message(stream, topic)
        new_topic = f"{stream}/{topic}"
        self.move_topic(msg["id"], self.config["ARCHIVE_STREAM"], new_topic)

    def get_last_message(self, stream, topic):
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
        response = self._bot.client.get_messages(request)
        return response["messages"][0]

    def move_topic(self, msg_id, stream, topic):
        client = self._bot.client
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
