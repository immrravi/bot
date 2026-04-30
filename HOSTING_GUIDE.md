# Hosting Your Instagram Reel Scraper Telegram Bot 24/7 for Free on Koyeb

This guide provides a step-by-step process to deploy your Instagram Reel Scraper Telegram bot on Koyeb, a serverless platform that offers a free tier suitable for running your bot 24/7. Koyeb supports Docker deployments, which is ideal for projects using Playwright.

## Table of Contents
1.  [Why Koyeb?](#why-koyeb)
2.  [Prerequisites](#prerequisites)
3.  [Prepare Your Project for Deployment](#prepare-your-project-for-deployment)
    *   [Update `requirements.txt`](#update-requirements.txt)
    *   [Create a `Dockerfile`](#create-a-dockerfile)
4.  [Set Up Your GitHub Repository](#set-up-your-github-repository)
5.  [Deploy to Koyeb](#deploy-to-koyeb)
    *   [Create a Koyeb Account](#create-a-koyeb-account)
    *   [Create a New Service](#create-a-new-service)
    *   [Configure Deployment](#configure-deployment)
    *   [Set Environment Variables](#set-environment-variables)
6.  [Monitor and Manage Your Bot](#monitor-and-manage-your-bot)
7.  [Important Considerations](#important-considerations)

## 1. Why Koyeb?

Koyeb is a developer-friendly serverless platform that allows you to deploy applications globally. Its free tier provides sufficient resources to run a Telegram bot continuously. Key advantages include:

*   **Always-On Free Tier**: Unlike some platforms that put free-tier services to sleep, Koyeb's free tier instances run 24/7 [1].
*   **Docker Support**: You can deploy applications using Dockerfiles, which is crucial for Playwright as it requires specific browser dependencies.
*   **Easy GitHub Integration**: Seamless deployment directly from your GitHub repository.
*   **Scalability**: While not strictly necessary for a single bot, Koyeb offers scalability options if your bot's usage grows.

## 2. Prerequisites

Before you begin, ensure you have the following:

*   **Your Instagram Reel Scraper Bot Code**: The `instagram_scraper` project with the `telegram_bot.py` file, `scraper.py`, `utils.py`, `excel.py`, `requirements.txt`, and `cookies.json`.
*   **GitHub Account**: You will need a GitHub account to host your bot's code. If you don't have one, sign up at [github.com](https://github.com/).
*   **Koyeb Account**: Sign up for a free Koyeb account at [koyeb.com](https://www.koyeb.com/).
*   **Telegram Bot Token**: Obtained from [@BotFather](https://t.me/botfather).
*   **`cookies.json`**: Your Instagram session cookies, as detailed in the project's `README.md`.

## 3. Prepare Your Project for Deployment

### Update `requirements.txt`

Ensure your `requirements.txt` file includes all necessary Python packages, especially `python-telegram-bot` and `playwright`. It should look something like this:

```
playwright==1.42.0
pandas==2.2.1
openpyxl==3.1.2
greenlet==3.0.3
python-telegram-bot==22.7
```

### Create a `Dockerfile`

A `Dockerfile` instructs Koyeb (or any Docker environment) on how to build and run your application. Create a file named `Dockerfile` in the root of your `instagram_scraper` project directory (the same directory as `telegram_bot.py`) with the following content:

```dockerfile
FROM mcr.microsoft.com/playwright/python:latest

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "telegram_bot.py"]
```

**Explanation of the `Dockerfile`:**

*   `FROM mcr.microsoft.com/playwright/python:latest`: This line specifies the base image. It uses an official Playwright Docker image that comes with Python and all necessary browser dependencies pre-installed, making it easy to run Playwright applications.
*   `WORKDIR /app`: Sets the working directory inside the Docker container to `/app`.
*   `COPY requirements.txt .`: Copies your `requirements.txt` file into the container.
*   `RUN pip install --no-cache-dir -r requirements.txt`: Installs all Python dependencies listed in `requirements.txt`. `--no-cache-dir` helps keep the image size smaller.
*   `COPY . .`: Copies all other files from your project directory into the `/app` directory in the container.
*   `CMD ["python3", "telegram_bot.py"]`: This is the command that will be executed when the Docker container starts. It runs your Telegram bot script.

## 4. Set Up Your GitHub Repository

1.  **Create a New Repository**: Go to [github.com/new](https://github.com/new) and create a new public or private repository. Give it a meaningful name (e.g., `instagram-reel-bot`).
2.  **Initialize Git**: In your local `instagram_scraper` project directory, initialize a Git repository:
    ```bash
    git init
    ```
3.  **Add Files**: Add all your project files to the repository:
    ```bash
    git add .
    ```
4.  **Commit Changes**: Commit your changes:
    ```bash
    git commit -m "Initial commit: Instagram Reel Scraper Telegram Bot"
    ```
5.  **Link to GitHub**: Link your local repository to the one you created on GitHub:
    ```bash
    git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git
    ```
    (Replace `YOUR_USERNAME` and `YOUR_REPOSITORY_NAME` with your actual GitHub username and repository name).
6.  **Push to GitHub**: Push your code to GitHub:
    ```bash
    git push -u origin main
    ```

## 5. Deploy to Koyeb

### Create a Koyeb Account

If you haven't already, sign up for a free account at [koyeb.com](https://www.koyeb.com/).

### Create a New Service

1.  Log in to your Koyeb Control Panel.
2.  Click on **Create Service**.

### Configure Deployment

1.  **Deployment Method**: Select **GitHub** as your deployment method.
2.  **Connect GitHub**: If you haven't already, connect your GitHub account to Koyeb and grant the necessary permissions.
3.  **Select Repository**: Choose the GitHub repository you just created (e.g., `instagram-reel-bot`).
4.  **Branch**: Select `main` (or the branch where your code resides).
5.  **Builder**: This is crucial. Change the builder type from `Buildpack` to **`Dockerfile`**.
6.  **App Name**: Give your application a name (e.g., `instagram-bot`).
7.  **Instance Type**: Ensure you select the **`Free`** instance type.

### Set Environment Variables

This is where you'll provide your Telegram Bot Token and Instagram cookies.

1.  In the Koyeb service configuration, navigate to the **Environment Variables** section.
2.  Add the following environment variables:
    *   **Key**: `TELEGRAM_BOT_TOKEN`
        **Value**: Your actual Telegram Bot Token (e.g., `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)
    *   **Key**: `COOKIES_JSON` (You will need to read your `cookies.json` file content and paste it here as a string)
        **Value**: The entire content of your `cookies.json` file as a single-line string. Make sure it's valid JSON.

    **Note on `cookies.json`**: While you can copy the `cookies.json` file directly into your Docker image, it's generally more secure to handle sensitive data like session cookies via environment variables, especially in public repositories. If your `cookies.json` is complex, you might need to adjust your Python code to read the cookies from an environment variable instead of a file. For simplicity, you can also include `cookies.json` directly in your GitHub repo if it's private, but be aware of the security implications.

    **Alternative for `cookies.json`**: If you prefer to keep `cookies.json` as a file and not expose its content as an environment variable, you can simply ensure `cookies.json` is present in your GitHub repository. The `Dockerfile` will copy it into the container.

3.  Click **Deploy** to start the deployment process.

## 6. Monitor and Manage Your Bot

Once deployed, Koyeb will build your Docker image and start your service. You can monitor the deployment status and view logs directly from the Koyeb Control Panel. If there are any issues, the logs will provide valuable debugging information.

## 7. Important Considerations

*   **Playwright Browser Installation**: The chosen base Docker image `mcr.microsoft.com/playwright/python:latest` already includes Playwright and its browser dependencies, so you don't need to run `playwright install` separately in your `Dockerfile`.
*   **Headless Mode**: Playwright will run in headless mode by default in the Docker container, which is suitable for server environments.
*   **Resource Limits**: While Koyeb offers a free tier, be mindful of its resource limits (CPU, RAM, bandwidth). If your bot experiences very high traffic or performs extremely intensive scraping, you might eventually hit these limits. However, for typical usage, the free tier should be sufficient.
*   **Error Handling**: Ensure your bot's code has robust error handling and logging to help diagnose issues when running 24/7.
*   **Updates**: When you update your bot's code on GitHub, Koyeb will automatically detect the changes and redeploy your service.

By following these steps, you should be able to successfully deploy your Instagram Reel Scraper Telegram bot to run 24/7 on Koyeb for free.

## References
[1] Koyeb Pricing: [https://www.koyeb.com/pricing](https://www.koyeb.com/pricing)
