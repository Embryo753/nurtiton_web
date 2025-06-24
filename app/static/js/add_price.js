// app/static/js/add_price.js

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('price-form');
    const submitBtn = document.getElementById('submit-btn');
    const submitBtnText = document.getElementById('submit-btn-text');
    const submitSpinner = document.getElementById('submit-spinner');

    function showLoadingState(isLoading) {
        if (isLoading) {
            submitBtn.disabled = true;
            submitBtnText.classList.add('d-none');
            submitSpinner.classList.remove('d-none');
        } else {
            submitBtn.disabled = false;
            submitBtnText.classList.remove('d-none');
            submitSpinner.classList.add('d-none');
        }
    }

    function displayFormErrors(errors) {
        // 清除所有舊的錯誤訊息和無效狀態
        document.querySelectorAll('.form-control.is-invalid, .form-select.is-invalid').forEach(el => el.classList.remove('is-invalid'));
        document.querySelectorAll('.invalid-feedback').forEach(el => el.textContent = '');

        // 顯示新的錯誤訊息
        for (const fieldName in errors) {
            const inputElement = document.getElementById(fieldName);
            if (inputElement) {
                inputElement.classList.add('is-invalid');
                const errorElement = document.getElementById(`error-${fieldName}`);
                if (errorElement) {
                    errorElement.textContent = errors[fieldName].join(', ');
                }
            }
        }
    }

    // 監聽所有表單輸入變化，實時清除錯誤
    form.querySelectorAll('.form-control, .form-select').forEach(input => {
        input.addEventListener('input', function() {
            if (this.classList.contains('is-invalid')) {
                this.classList.remove('is-invalid');
                const errorElement = document.getElementById(`error-${this.id}`);
                if (errorElement) {
                    errorElement.textContent = '';
                }
            }
        });
    });

    // 處理表單提交
    form.addEventListener('submit', function(event) {
        event.preventDefault(); // 阻止默認的表單提交行為
        
        showLoadingState(true); // 顯示載入狀態
        displayFormErrors({}); // 清除所有錯誤

        const formData = {
            ingredient_name: document.getElementById('ingredient_name').value,
            source: document.getElementById('source').value,
            price: document.getElementById('price').value,
            quantity: document.getElementById('quantity').value,
            unit: document.getElementById('unit').value,
            // CSRF Token for Flask-WTF
            csrf_token: document.querySelector('input[name="csrf_token"]').value
        };

        fetch(form.action, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert(data.message);
                // --- 修改處：使用後端回傳的 URL 進行跳轉 ---
                window.location.href = data.redirect_url;
            } else {
                alert('新增價格紀錄失敗: ' + (data.message || '請檢查表單欄位。'));
                if (data.errors) {
                    displayFormErrors(data.errors);
                }
            }
        })
        .catch(error => {
            console.error('Error submitting form:', error);
            alert('提交表單時發生網路或伺服器錯誤。');
        })
        .finally(() => {
            showLoadingState(false);
        });
    });
});
