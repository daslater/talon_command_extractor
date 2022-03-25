from talon import Module, actions, registry
import sys, os, json


class CommandGroup:
    def __init__(self, file, context, commands):
        self.file = file
        self.context = context
        self.commands = commands


def key_commands(list_name):
    command_list = registry.lists[list_name][0]
    return CommandGroup('code/keys.py', list_name, command_list)


def formatters():
    command_list = registry.lists['user.formatters'][0]
    command_list = {key: actions.user.formatted_text(f"example of formatting with {key}", key) for key in command_list}
    return CommandGroup("code/formatters.py", "user.formatters", command_list)


def context_commands(commands):
    # write out each command and its implementation
    rules = {}
    for key in commands:
        try:
            rule = commands[key].rule.rule
            implementation = commands[key].target.code  # .replace("\n", "\n\t\t")
        except Exception:
            continue
        lines = [line for line in implementation.split("\n") if line and line[0] != "#"]
        rules[rule] = "\n".join(lines)

    return rules


def format_context_name(name):
    # The logic here is intended to only get contexts from talon files that have actual voice commands.
    splits = name.split(".")
    index = -1

    os = ""

    if "mac" in splits:
        os = "mac "
    if "win" in splits:
        os = "win "
    if "linux" in splits:
        os = "linux "

    if "talon" in splits[index]:
        index = -2
        short_name = splits[index].replace("_", " ")
    else:
        short_name = splits[index].replace("_", " ")

    if "mac" == short_name or "win" == short_name or "linux" == short_name:
        index = index - 1
        short_name = splits[index].replace("_", " ")

    return f"{os}{short_name}"


def format_file_name(name):
    splits = name.split(".")
    base_file_name = "/".join(splits[2:-1])
    extension = splits[-1]

    return f"{base_file_name}.{extension}"


def resolve_dup(full_name1, full_name2, formatted_name):
    splits1 = full_name1.split("/")
    splits2 = full_name2.split("/")

    index = -2
    while splits1[index] == splits2[index]:
        index -= 1

    return f"{formatted_name} ({splits1[index]})", f"{formatted_name} ({splits2[index]})"


mod = Module()


@mod.action_class
class user_actions:
    def json_commands():
        """Creates a JSON file of talon commands"""

        key_command_names = ['user.letter', 'user.number_key', 'user.modifier_key', 'user.special_key',
                             'user.symbol_key', 'user.arrow_key', 'user.punctuation', 'user.function_key']

        # Storing these in a dict makes it easier to detect duplicates
        command_groups = {name: key_commands(name) for name in key_command_names}

        # get all the commands in all the contexts
        list_of_contexts = registry.contexts.items()
        for name, context in list_of_contexts:
            commands = context.commands  # Get all the commands from a context
            if len(commands) > 0:
                context_name = format_context_name(name)
                file_name = format_file_name(name)

                # If this context name is a duplicate, create new names and update the dict
                if context_name in command_groups:
                    other = command_groups.pop(context_name)
                    other.context, context_name = resolve_dup(other.file, file_name, context_name)
                    command_groups[other.context] = other

                command_groups[context_name] = CommandGroup(file_name, context_name, context_commands(commands))

        this_dir = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(this_dir, 'talon_commands.json')
        with open(file_path, "w") as write_file:
            json.dump([command_group.__dict__ for command_group in command_groups.values()], write_file, indent=4)
