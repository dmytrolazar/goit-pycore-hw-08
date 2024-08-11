from collections import UserDict
from datetime import datetime, timedelta
import pickle

class InvalidPhoneNumberException(Exception):
    pass

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    def __init__(self, value):
        super().__init__(value)

class Phone(Field):
    def __init__(self, value):
        if len(value) == 10 and all(x.isdigit() for x in value[::1]):
            super().__init__(value)
        else:
            raise InvalidPhoneNumberException()
        
    def __str__(self):
        return f"{self.value}"

class Birthday(Field):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")    

    def __str__(self):
        return f"{self.value.strftime("%d.%m.%Y")}"

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))
    
    def edit_phone(self, oldphone, newphone):
        phones = []
        for phone in self.phones:
            if phone.value == oldphone:
                phone.value = newphone
            phones.append(phone)
        self.phones = phones
    
    def remove_phone(self, phone_to_remove):
        phones = []
        for phone in self.phones:
            if phone.value != phone_to_remove:
                phones.append(phone)
        self.phones = phones

    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p
            
    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        return f"Contact name: {self.name.value}, birthday: {self.birthday or "No birthday specified"}, phones: {'; '.join(p.value for p in self.phones)}"


def get_days_from_today(date):
    today = datetime.today().date()
    return (today - date).days

class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name) -> Record:
        try:
            return self.data[name]
        except KeyError:
            return None
    
    def delete(self, name):
        self.data.pop(name)

    def get_upcoming_birthdays(self):
        users_to_congratulate = []
        for name, record in self.data.items():
            if not record.birthday:
                continue
            users_next_birthday = record.birthday.value
            users_next_birthday = datetime(year = datetime.today().year, month = users_next_birthday.month, day = users_next_birthday.day).date()
            if users_next_birthday < datetime.today().date():
                users_next_birthday = datetime(year = datetime.today().year + 1, month = users_next_birthday.month, day = users_next_birthday.day).date()
            users_next_birthday_in = get_days_from_today(users_next_birthday)
            if users_next_birthday_in > 0 or users_next_birthday_in <= -7:
                continue
            else:
                congratulation_day = users_next_birthday
                if users_next_birthday.weekday() == 5:
                    congratulation_day += timedelta(days = 2)
                elif users_next_birthday.weekday() == 6:
                    congratulation_day += timedelta(days = 1)
                user_dict = {}
                user_dict["name"] = name
                user_dict["users_next_birthday"] = datetime.strftime(users_next_birthday, "%Y.%m.%d")
                user_dict["congratulation_date"] = datetime.strftime(congratulation_day, "%Y.%m.%d")
                users_to_congratulate.append(user_dict)
        return "Users to congratulate next week:\r\n" + "\r\n".join(f"{user["name"]}: congratulate on {user["congratulation_date"]}, next birthday on {user["users_next_birthday"]}" for user in users_to_congratulate)

def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args

def input_error_add_contact(func):
    def inner(*args, **kwargs):
        try:
            if len(args[0]) != 2:
                return "Enter name and phone to add a contact."
            return func(*args, **kwargs)
        except InvalidPhoneNumberException:
            return "Enter a valid phone number."
    return inner

@input_error_add_contact
def add_contact(args, contacts: AddressBook):
    name, phone = args
    record = contacts.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        contacts.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message

def input_error_change_contact(func):
    def inner(*args, **kwargs):
        if len(args[0]) != 3:
            return "Enter name, old phone and new phone to change a contact."
        return func(*args, **kwargs)
    return inner

@input_error_change_contact
def change_contact(args, contacts: AddressBook):
    name, old_phone, new_phone = args
    record = contacts.find(name)
    if record:
        if record.find_phone(old_phone):
            record.edit_phone(old_phone, new_phone)
            return "Contact updated."
        else:
            return "Phone doesn't exist."
    else:
        return "Contact doesn't exist."

def input_error_show_contact(func):
    def inner(*args, **kwargs):
        try:
            if len(args[0]) != 1:
                return "Enter a name of a contact to show."
            return func(*args, **kwargs)
        except KeyError:
            return "Contact doesn't exist."
    return inner

@input_error_show_contact
def show_contact(args, contacts: AddressBook):
    if contacts.find(args[0]):
        return "; ".join(p.value for p in contacts.find(args[0]).phones)
    else:
        return "Contact doesn't exist."

def show_all_contacts(contacts: AddressBook):
    return "\r\n".join(str(record) for _, record in contacts.items()) if contacts.items() else "Your contact list is empty."

def input_error_add_birthday(func):
    def inner(*args, **kwargs):
        if len(args[0]) != 2:
            return "Enter name and birthday to add a birthday."
        return func(*args, **kwargs)
    return inner

@input_error_add_birthday
def add_birthday(args, contacts: AddressBook):
    name, birthday = args
    try:
        if contacts.find(name):
            contacts.find(name).add_birthday(birthday)
            return "Contact updated."
        else:
            return "Contact doesn't exist."
    except ValueError:
        return "Enter a valid birthday."

def input_error_show_birthday(func):
    def inner(*args, **kwargs):
        try:
            if len(args[0]) != 1:
                return "Enter a name of a contact."
            return func(*args, **kwargs)
        except KeyError:
            return "Contact doesn't exist."
    return inner

@input_error_show_birthday
def show_birthday(args, contacts: AddressBook):
    if contacts.find(args[0]):
        return str(contacts.find(args[0]).birthday or "No birthday specified")
    else:
        return "Contact doesn't exist."

def birthdays(contacts: AddressBook):
    return contacts.get_upcoming_birthdays()

def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()  # Повернення нової адресної книги, якщо файл не знайдено

def main():
    book = load_data()
    
    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, *args = parse_input(user_input)

        if command in ["close", "exit"] and len(args) == 0:
            print("Good bye!")
            break
        elif command == "hello" and len(args) == 0:
            print("How can I help you?")
        elif command == "add":
            print(add_contact(args, book))
        elif command == "change":
            print(change_contact(args, book))
        elif command == "phone":
            print(show_contact(args, book))
        elif command == "all" and len(args) == 0:
            print(show_all_contacts(book))
        elif command == "add-birthday":
            print(add_birthday(args, book))
        elif command == "show-birthday":
            print(show_birthday(args, book))
        elif command == "birthdays":
            print(birthdays(book))
        else:
            print("Invalid command.")

    save_data(book)

if __name__ == "__main__":
    main()