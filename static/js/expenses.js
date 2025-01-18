document.addEventListener('DOMContentLoaded', function() {
    // Initialiser la date à aujourd'hui
    document.getElementById('expense-date').valueAsDate = new Date();
    
    // Charger les dépenses existantes
    loadExpenses();
    
    // Gérer la soumission du formulaire
    document.getElementById('expense-form').addEventListener('submit', async function(event) {
        event.preventDefault();
        
        const formData = new FormData(this);
        
        try {
            const response = await fetch('/add_expense', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            if (result.success) {
                showNotification('success', get_text('expense_added_success'));
                this.reset();
                document.getElementById('expense-date').valueAsDate = new Date();
                loadExpenses();
            } else {
                showNotification('error', result.message);
            }
        } catch (error) {
            showNotification('error', get_text('error_adding_expense'));
        }
    });
});

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
            } else {
                showNotification('error', result.message);
            }
        } catch (error) {
            showNotification('error', get_text('error_deleting_expense'));
        }
    }
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString();
}

function formatAmount(amount) {
    return parseFloat(amount).toFixed(2);
}

function showNotification(type, message) {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type}`;
    notification.style.display = 'block';
    
    setTimeout(() => {
        notification.style.display = 'none';
    }, 3000);
}
