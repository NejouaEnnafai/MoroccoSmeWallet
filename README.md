# Morocco SME Wallet 🇲🇦

A modern digital wallet solution tailored for Moroccan Small and Medium Enterprises (SMEs). This Flask-based application provides essential financial management tools with support for Arabic language and Moroccan business requirements.

## Features 🌟

- **Bilingual Support**: Full Arabic and French language support
- **Secure Authentication**: Multi-factor authentication for business accounts
- **Transaction Management**: Easy-to-use interface for deposits, withdrawals, and transfers
- **Financial Dashboard**: Real-time analytics and transaction history
- **Mobile Responsive**: Optimized for both desktop and mobile devices
- **QR Code Integration**: Quick payment generation and scanning
- **Business Tools**: Invoice generation, expense tracking, and financial reports
- **Compliance**: Adherence to Moroccan financial regulations

## Technical Stack 💻

- **Backend**: Python Flask
- **Database**: SQLAlchemy with SQLite (easily upgradable to PostgreSQL)
- **Frontend**: Bootstrap 5, Chart.js
- **Authentication**: Flask-Login
- **Localization**: Flask-Babel
- **Security**: JWT, bcrypt

## Quick Start 🚀

1. Clone the repository:
```bash
git clone https://github.com/yourusername/morocco-sme-wallet.git
cd morocco-sme-wallet
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize the database:
```bash
flask db upgrade
```

6. Run the application:
```bash
flask run
```

Visit `http://localhost:5000` in your browser.

## Development Setup 🛠️

1. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Run tests:
```bash
pytest
```

3. Check code style:
```bash
flake8
black .
```

## Contributing 🤝

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License 📝

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments 🙏

- Moroccan SME community for valuable feedback
- Flask and Python community for excellent documentation
- All contributors who help improve this project

## Contact 📧

For questions and support, please open an issue or contact the maintainers.

---

Made with ❤️ for Moroccan SMEs
