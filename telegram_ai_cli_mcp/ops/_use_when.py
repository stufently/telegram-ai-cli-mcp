"""When to call each published tool, in the words the model should see.

The MCP description is what an agent reads before it picks a tool. Each entry
is one or two sentences: the situation that should reach this tool, and, where
a neighbour does the nearby job, the name of that neighbour. ``mcp_server``
inserts the sentence after the opening line of the operation's own description.
Keyed by operation name so a renamed tool does not silently keep the old advice.
"""

from __future__ import annotations

USE_WHEN: dict[str, str] = {
    "chats.list": (
        "Use when the user wants a chat list, unread counts, or a chat id from a title. "
        "Do not use this to read messages; call telegram_chat_read once the chat is known, "
        "or telegram_search to find text."
    ),
    "chat.read": (
        "Use when the user asks what was said in one known chat. Do not use this to find "
        "a chat by name; call telegram_chats first, or telegram_search when the words "
        "matter more than the latest page. Reading does not mark the chat read; that is "
        "telegram_plan_mark_read."
    ),
    "chat.members": (
        "Use when the user asks who is in a group or channel, or which members are admins. "
        "Do not use this to resolve one username; call telegram_whois, or telegram_chat_read "
        "to see what those people wrote."
    ),
    "inbox.list": (
        "Use when the user asks what is waiting, what they missed, or which chats need a "
        "reply. Do not use this to read one chat's history; call telegram_chat_read, or "
        "telegram_mentions when the question is who mentioned them."
    ),
    "search.messages": (
        "Use when the user asks to find messages by words, in one chat or across the "
        "account. Do not use this for a regular expression or for text already copied "
        "locally; call telegram_archive_search for that, or telegram_chat_read to page "
        "the latest history."
    ),
    "contacts.whois": (
        "Use when the user gives a username, numeric id, or invite link and asks who or "
        "what it is. Do not use this to join the chat; joining is telegram_plan_join_chat, "
        "and a member list is telegram_chat_members."
    ),
    "fleet.list": (
        "Use when the user asks which Telegram accounts are configured, signed in, or "
        "locked. Do not use this to list devices on one account; call telegram_sessions, "
        "or telegram_chats to see that account's dialogs."
    ),
    "folders.list": (
        "Use when the user asks how their chat folders are set up or which folder id to "
        "filter by. Do not use this to put a chat into a folder; that is "
        "telegram_plan_folder_add, and listing the chats in one folder is telegram_chats "
        "with a folder argument."
    ),
    "mentions.list": (
        "Use when the user asks where they were mentioned or which of their messages got "
        "a reaction. Do not use this for a ranked overview of every unread chat; call "
        "telegram_inbox, or telegram_message_reactions for the counts on one known message."
    ),
    "message.reactions": (
        "Use when the user asks how people reacted to one message. Do not use this to add "
        "or remove a reaction; those are telegram_plan_react_message and "
        "telegram_plan_unreact_message, and unread reactions across chats are "
        "telegram_mentions."
    ),
    "chat.topics": (
        "Use when the user asks for the topic list of a forum, or which topic id to read. "
        "Do not use this to read the messages inside a topic; call telegram_chat_read "
        "with that topic id."
    ),
    "watch.wait": (
        "Use when the user wants to wait for the next message instead of asking again. "
        "Do not use this to look at what already arrived; call telegram_inbox or "
        "telegram_chat_read. The call holds the account until it returns."
    ),
    "drafts.list": (
        "Use when the user asks about text they started and never sent. Do not use this "
        "for messages queued to go out later; call telegram_scheduled, or "
        "telegram_chat_read for messages that were actually sent."
    ),
    "scheduled.list": (
        "Use when the user asks what is queued to send later in one chat. Do not use this "
        "for unsent drafts; call telegram_drafts, or telegram_plan_schedule_message to "
        "queue a new message."
    ),
    "account.sessions": (
        "Use when the user asks which devices or apps are signed in, or whether one of "
        "them is unfamiliar. Do not use this to end a session; this server has no such "
        "tool, and telegram_fleet only says whether the local account is usable."
    ),
    "media.fetch": (
        "Use when the user wants the file attached to one message saved on this machine. "
        "Do not use this to turn a voice message into text; call telegram_media_transcribe, "
        "or telegram_chat_read when the attachment metadata is enough."
    ),
    "media.transcribe": (
        "Use when the user asks what a voice message or audio file says. Do not use this "
        "only to download the file; call telegram_media_fetch, and do not use it for an "
        "ordinary text message; call telegram_chat_read."
    ),
    "archive.sync": (
        "Use when the user wants one chat copied to the local archive so later questions "
        "do not hit Telegram. Do not use this to search that copy; call "
        "telegram_archive_search after a sync, or telegram_chat_read for a live page."
    ),
    "archive.search": (
        "Use when the user wants a regular expression, a sender, or a date range over "
        "messages already archived. Do not use this for a live Telegram search; call "
        "telegram_search, or telegram_archive_sync first when the chat is not archived."
    ),
    "archive.status": (
        "Use when the user asks what the local archive holds, how many messages, or when "
        "a chat was last synced. Do not use this to search the text; call "
        "telegram_archive_search, or telegram_archive_forget to erase a chat from disk."
    ),
    "archive.forget": (
        "Use when the user wants one chat's archived messages erased from this machine. "
        "Do not use this to leave the chat on Telegram; call telegram_plan_leave_chat, "
        "or telegram_archive_status to see what is stored first."
    ),
    "message.send": (
        "Use when the user asks to send a new message and a person will apply the plan. "
        "Do not use this to reply to one existing message; call telegram_plan_reply_message, "
        "or telegram_plan_schedule_message when it should wait."
    ),
    "message.reply": (
        "Use when the user asks to answer one specific message. Do not use this for a "
        "new message that is not a reply; call telegram_plan_send_message."
    ),
    "message.send_file": (
        "Use when the user asks to send a file that is already in the uploads directory. "
        "Do not use this to download an attachment; call telegram_media_fetch, or "
        "telegram_plan_send_message for text alone."
    ),
    "message.edit": (
        "Use when the user asks to change the text of a message this account already sent. "
        "Do not use this to delete it; call telegram_plan_delete_message, or "
        "telegram_plan_send_message to post a new one."
    ),
    "message.delete": (
        "Use when the user asks to delete messages this account sent. Do not use this to "
        "edit the wording; call telegram_plan_edit_message, or telegram_archive_forget "
        "to erase a local archive copy."
    ),
    "message.forward": (
        "Use when the user asks to forward existing messages into another chat. Do not "
        "use this to compose a new message; call telegram_plan_send_message."
    ),
    "chat.mark_read": (
        "Use when the user explicitly asks to mark a chat read. Do not use this while "
        "only looking; telegram_chat_read never marks a chat seen."
    ),
    "chat.join": (
        "Use when the user asks to join a public chat or open an invite link. Do not use "
        "this only to see what the link points at; call telegram_whois, or "
        "telegram_plan_leave_chat to leave."
    ),
    "chat.leave": (
        "Use when the user asks to leave a group or channel. Do not use this to hide it "
        "in the Archived list; call telegram_plan_archive_chat, or telegram_plan_kick_user "
        "to remove someone else."
    ),
    "chat.create": (
        "Use when the user asks to create a new supergroup or a broadcast channel. Do not "
        "use this to join one that already exists; call telegram_plan_join_chat."
    ),
    "chat.invite": (
        "Use when the user asks to add one person to a chat. Do not use this to grant "
        "them admin rights; call telegram_plan_promote_admin, or telegram_plan_ban_user "
        "to stop them returning."
    ),
    "chat.promote": (
        "Use when the user asks to grant admin rights to one member. Do not use this to "
        "take rights away; call telegram_plan_demote_admin, or telegram_plan_restrict_user "
        "for a temporary limit that is not an admin title."
    ),
    "chat.ban": (
        "Use when the user asks to ban one member so they cannot return. Do not use this "
        "for a removal that still lets them rejoin; call telegram_plan_kick_user, or "
        "telegram_plan_unban_user to undo a ban."
    ),
    "chat.unban": (
        "Use when the user asks to lift a ban or every restriction on one member. Do not "
        "use this to remove an admin title; call telegram_plan_demote_admin. It does not "
        "invite the person back."
    ),
    "chat.kick": (
        "Use when the user asks to remove one member without banning them. Do not use "
        "this when they must be blocked from returning; call telegram_plan_ban_user."
    ),
    "chat.restrict": (
        "Use when the user asks to take specific rights from one member for a time. Do "
        "not use this to ban them outright; call telegram_plan_ban_user, or "
        "telegram_plan_unban_user to lift the restriction."
    ),
    "chat.demote": (
        "Use when the user asks to take every admin right away from one member. Do not "
        "use this to remove them from the chat; call telegram_plan_kick_user, or "
        "telegram_plan_promote_admin to grant rights."
    ),
    "account.profile": (
        "Use when the user asks to change this account's own name, bio, or username. Do "
        "not use this to rename a chat; call telegram_plan_set_chat_title."
    ),
    "account.block": (
        "Use when the user asks to block one person from contacting this account. Do not "
        "use this to ban them from a group; call telegram_plan_ban_user, or "
        "telegram_plan_unblock_user to undo the block."
    ),
    "account.unblock": (
        "Use when the user asks to let one person contact this account again. Do not use "
        "this to lift a ban inside a chat; call telegram_plan_unban_user."
    ),
    "chat.set_title": (
        "Use when the user asks to rename a group or channel. Do not use this to change "
        "the account's own name; call telegram_plan_set_profile, or "
        "telegram_plan_set_chat_about for the description."
    ),
    "chat.set_about": (
        "Use when the user asks to change or clear a chat's description. Do not use this "
        "to rename the chat; call telegram_plan_set_chat_title."
    ),
    "chat.set_photo": (
        "Use when the user asks to replace a chat's photo with an image from the uploads "
        "directory. Do not use this to send that image as a message; call "
        "telegram_plan_send_file."
    ),
    "message.react": (
        "Use when the user asks to put an emoji reaction on a message. Do not use this "
        "to read who already reacted; call telegram_message_reactions, or "
        "telegram_plan_unreact_message to take a reaction off."
    ),
    "message.unreact": (
        "Use when the user asks to take this account's reaction off a message. Do not "
        "use this to add one; call telegram_plan_react_message."
    ),
    "message.pin": (
        "Use when the user asks to pin a message for the chat. Do not use this to unpin; "
        "call telegram_plan_unpin_message. A pin notifies members unless it is silent."
    ),
    "message.unpin": (
        "Use when the user asks to unpin a message. Do not use this to pin one; call "
        "telegram_plan_pin_message."
    ),
    "message.schedule": (
        "Use when the user asks to send a message later, or when the other person is next "
        "online. Do not use this to send now; call telegram_plan_send_message, or "
        "telegram_scheduled to see what is already queued."
    ),
    "chat.archive": (
        "Use when the user asks to move a chat into Archived or back to the main list. "
        "Do not use this to mute it; call telegram_plan_mute_chat, or "
        "telegram_plan_leave_chat to leave."
    ),
    "chat.mute": (
        "Use when the user asks to mute or unmute a chat's notifications. Do not use this "
        "to ban or block anyone; call telegram_plan_ban_user or telegram_plan_block_user, "
        "or telegram_plan_archive_chat to hide the chat."
    ),
    "folders.add": (
        "Use when the user asks to put one chat into a folder. Do not use this to see "
        "the folders; call telegram_folders, or telegram_chats with a folder argument "
        "to list what is already in one."
    ),
}
