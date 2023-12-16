## Contributing Guidelines

I welcome contributions from everyone who is interested in improving the **Tempus** project! Below are some
guidelines to help you contribute effectively.

### Getting Started

1. **Fork the Repository**: Fork the Tempus repository to your own GitHub account.
2. **Clone the Forked Repo**: Clone your fork locally on your computer.
    ```bash
    git clone https://github.com/vvvlladimir/Tempus.git
    ```
3. **Add Upstream**: Add the original repository as an upstream to fetch updates.
    ```bash
    git remote add upstream https://github.com/vvvlladimir/Tempus.git
    ```

### Making Changes

1. **Checkout `dev` Branch**: Before creating a new branch, make sure you are in the `dev` branch.
    ```bash
    git checkout dev
    ```
2. **Create a New Branch**: Always create a new branch for your work.
    ```bash
    git checkout -b feature/your-feature-name
    ```
3. **Make Your Changes**: Implement your feature or bug fix.
4. **Commit Changes**: Commit your changes. Write a clear and meaningful commit message describing what you did.
    ```bash
    git commit -m "Your detailed commit message"
    ```
5. **Sync Fork with `dev`**: Fetch updates from the upstream `dev` branch.
    ```bash
    git pull upstream dev
    ```
6. **Push to Your Fork**: Push your changes to your fork on GitHub.
    ```bash
    git push origin feature/your-feature-name
    ```

### Submitting a Pull Request

1. **Open a Pull Request**: Go to the original Tempus repository and click on "New Pull Request."
2. **Base Branch**: Ensure the base branch is set to `dev` as we require all changes to be merged into `dev` first due
   to its protected status.
3. **Compare Changes**: Select your feature branch from your fork.
4. **Submit the Pull Request**: Provide a comprehensive description of the changes and click on "Create pull request."
5. **Address Feedback**: If your PR receives feedback, make the required changes and update the PR.

### Code Style and Linting

Please adhere to the existing coding style and conventions. Make sure to run any linters if the project has them.

### Documentation

If your changes involve adding or modifying features, please update the documentation accordingly.

---

By following these guidelines, you'll make it easier for your contributions to be reviewed and merged. Thank you for
contributing to **Tempus**!
