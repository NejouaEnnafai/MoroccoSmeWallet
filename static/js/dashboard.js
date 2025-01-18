document.addEventListener('DOMContentLoaded', function() {
    // Initialisation du graphique
    const ctx = document.getElementById('expenseChart').getContext('2d');
    const expenseChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: [{
                label: 'Monthly Expenses',
                data: [12000, 19000, 15000, 25000, 22000, 30000],
                borderColor: 'rgba(255, 215, 0, 1)',
                backgroundColor: 'rgba(255, 215, 0, 0.1)',
                borderWidth: 2,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)'
                    }
                }
            }
        }
    });

    // Gestion du formulaire d'ajout de dépense
    const addExpenseForm = document.getElementById('addExpenseForm');
    addExpenseForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        fetch('/api/expenses', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(Object.fromEntries(formData))
        })
        .then(response => response.json())
        .then(data => {
            window.location.reload();
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });

    // Gestion des boutons d'édition et de suppression
    document.querySelectorAll('[data-expense-id]').forEach(button => {
        button.addEventListener('click', function() {
            const expenseId = this.getAttribute('data-expense-id');
            if (this.querySelector('.fa-trash')) {
                if (confirm('Are you sure you want to delete this expense?')) {
                    fetch(`/api/expenses/${expenseId}`, {
                        method: 'DELETE'
                    }).then(() => window.location.reload());
                }
            }
        });
    });

    // Fonctions pour la gestion des revenus
    function showRevenueModal() {
        document.getElementById('revenue-modal').style.display = 'block';
        document.getElementById('revenue-date').valueAsDate = new Date();
    }

    function hideRevenueModal() {
        document.getElementById('revenue-modal').style.display = 'none';
        document.getElementById('revenue-form').reset();
    }

    async function addRevenue(event) {
        event.preventDefault();
        const formData = {
            amount: parseFloat(document.getElementById('revenue-amount').value),
            category: document.getElementById('revenue-category').value,
            description: document.getElementById('revenue-description').value,
            date: document.getElementById('revenue-date').value
        };

        try {
            const response = await fetch('/add_revenue', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();
            if (result.success) {
                showNotification('success', get_text('revenue_added_success'));
                hideRevenueModal();
                loadRevenues();
                updateDashboardStats();
            } else {
                showNotification('error', result.message);
            }
        } catch (error) {
            showNotification('error', get_text('error_adding_revenue'));
        }
    }

    async function loadRevenues() {
        try {
            const response = await fetch('/get_revenues');
            const revenues = await response.json();
            
            const tbody = document.getElementById('revenues-body');
            tbody.innerHTML = '';
            
            revenues.forEach(revenue => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${formatDate(revenue.date)}</td>
                    <td>${revenue.category}</td>
                    <td>${revenue.description}</td>
                    <td class="amount">${formatAmount(revenue.amount)} MAD</td>
                `;
                tbody.appendChild(row);
            });
        } catch (error) {
            showNotification('error', get_text('error_loading_revenues'));
        }
    }

    // Fonctions pour la gestion des dépenses
    function showExpenseModal() {
        document.getElementById('expense-modal').style.display = 'block';
        document.getElementById('expense-date').valueAsDate = new Date();
    }

    function hideExpenseModal() {
        document.getElementById('expense-modal').style.display = 'none';
        document.getElementById('expense-form').reset();
    }

    async function addExpense(event) {
        event.preventDefault();
        const formData = new FormData();
        formData.append('amount', document.getElementById('expense-amount').value);
        formData.append('category', document.getElementById('expense-category').value);
        formData.append('description', document.getElementById('expense-description').value);
        formData.append('date', document.getElementById('expense-date').value);
        
        const receiptFile = document.getElementById('expense-receipt').files[0];
        if (receiptFile) {
            formData.append('receipt', receiptFile);
        }

        try {
            const response = await fetch('/add_expense', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            if (result.success) {
                showNotification('success', get_text('expense_added_success'));
                hideExpenseModal();
                loadExpenses();
                updateDashboardStats();
            } else {
                showNotification('error', result.message);
            }
        } catch (error) {
            showNotification('error', get_text('error_adding_expense'));
        }
    }

    async function loadExpenses() {
        try {
            const response = await fetch('/get_expenses');
            const expenses = await response.json();
            
            const tbody = document.getElementById('expenses-body');
            tbody.innerHTML = '';
            
            expenses.forEach(expense => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${formatDate(expense.date)}</td>
                    <td>${expense.category}</td>
                    <td>${expense.description}</td>
                    <td class="amount">${formatAmount(expense.amount)} MAD</td>
                    <td class="actions">
                        ${expense.receipt_path ? 
                            `<a href="/uploads/${expense.receipt_path}" target="_blank" class="action-btn">
                                <i class="fas fa-receipt"></i>
                            </a>` : ''}
                        <button onclick="deleteExpense(${expense.id})" class="action-btn delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        } catch (error) {
            showNotification('error', get_text('error_loading_expenses'));
        }
    }

    async function deleteExpense(id) {
        if (confirm(get_text('confirm_delete_expense'))) {
            try {
                const response = await fetch(`/delete_expense/${id}`, {
                    method: 'DELETE'
                });
                
                const result = await response.json();
                if (result.success) {
                    showNotification('success', get_text('expense_deleted_success'));
                    loadExpenses();
                    updateDashboardStats();
                } else {
                    showNotification('error', result.message);
                }
            } catch (error) {
                showNotification('error', get_text('error_deleting_expense'));
            }
        }
    }

    // Mettre à jour les statistiques du dashboard pour inclure les revenus
    async function updateDashboardStats() {
        try {
            const [expensesResponse, revenuesResponse] = await Promise.all([
                fetch('/get_expenses'),
                fetch('/get_revenues')
            ]);
            
            const expenses = await expensesResponse.json();
            const revenues = await revenuesResponse.json();
            
            const totalExpenses = expenses.reduce((sum, exp) => sum + exp.amount, 0);
            const totalRevenues = revenues.reduce((sum, rev) => sum + rev.amount, 0);
            const balance = totalRevenues - totalExpenses;
            
            document.getElementById('total-revenue').textContent = `${formatAmount(totalRevenues)} MAD`;
            document.getElementById('total-expenses').textContent = `${formatAmount(totalExpenses)} MAD`;
            document.getElementById('balance').textContent = `${formatAmount(balance)} MAD`;
            
            // Mise à jour des graphiques si nécessaire
            updateCharts(expenses, revenues);
        } catch (error) {
            console.error('Error updating dashboard stats:', error);
        }
    }

    // Initialisation
    loadRevenues();
    loadExpenses();
    updateDashboardStats();
});
