# Bookclub Bot

This repository contains a bot for managing a book club. The bot can handle various tasks such as managing users, tracking daily and weekly activities, and more.

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/Robben1972/bookclub.git
    cd bookclub
    ```

2. Create a virtual environment and activate it:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required libraries:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

Create a `.env` file in the root directory of the project and add the following fields:

```env
TOKEN=""
GROUP_ID=""
USERS_FILE=""
DAILY_FILE=""
WEEKLY_FILE=""
LEFT_FILE=""
BOOKS_FILE=""

ADMIN1=""
ADMIN2=""
ADMIN3=""
```

Fill in the values for each field as per your requirements.

## Running the Bot

To run the bot, use the following command:

```bash
python main2.py
```

Make sure to activate your virtual environment before running the bot.

## Contributing

Feel free to fork this repository and submit pull requests. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
```

You can add this to a file named `README.md` in your repository. Let me know if you need any more help!
