// app/static/js/add_price.js

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('price-form');
    const submitBtn = document.getElementById('submit-btn');
    const submitBtnText = document.getElementById('submit-btn-text');
    const submitSpinner = document.getElementById('submit-spinner');

    // --- ★ 新增：自動完成功能的 DOM 元素 ---
    const ingredientNameInput = document.getElementById('ingredient_name');
    const searchResultsContainer = document.getElementById('ingredient-search-results');
    let searchTimeout;

    // --- ★ 新增：即時搜尋邏輯 ---
    ingredientNameInput.addEventListener('input', function() {
        // 清除上一次的計時器，避免在快速打字時發送過多請求
        clearTimeout(searchTimeout);
        const query = this.value.trim();

        // 如果輸入框是空的，就清空搜尋結果
        if (query.length < 1) {
            searchResultsContainer.innerHTML = '';
            return;
        }

        // 設定一個延遲 (300毫秒)，在使用者停止打字後才發送請求
        searchTimeout = setTimeout(() => {
            fetch(`/pricing/api/search_all_ingredients?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    searchResultsContainer.innerHTML = ''; // 先清空舊結果
                    if (data.length > 0) {
                        data.forEach(item => {
                            const resultItem = document.createElement('a');
                            resultItem.href = '#';
                            resultItem.className = 'list-group-item list-group-item-action';
                            resultItem.textContent = item.name;
                            
                            // 當使用者點擊搜尋結果時
                            resultItem.addEventListener('click', function(e) {
                                e.preventDefault(); // 防止頁面跳轉
                                ingredientNameInput.value = this.textContent; // 將點選的名稱填入輸入框
                                searchResultsContainer.innerHTML = ''; // 清空並隱藏結果列表
                            });
                            searchResultsContainer.appendChild(resultItem);
                        });
                    }
                })
                .catch(error => console.error('Error during ingredient search:', error));
        }, 300); 
    });

    // 當使用者點擊頁面其他地方時，隱藏搜尋結果列表
    document.addEventListener('click', function(e) {
        if (!ingredientNameInput.contains(e.target)) {
            searchResultsContainer.innerHTML = '';
        }
    });
    // --- 即時搜尋邏輯結束 ---


    // --- 原有的表單提交邏輯 (保持不變) ---
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
        document.querySelectorAll('.form-control.is-invalid, .form-select.is-invalid').forEach(el => el.classList.remove('is-invalid'));
        document.querySelectorAll('.invalid-feedback').forEach(el => el.textContent = '');

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

    form.addEventListener('submit', function(event) {
        event.preventDefault();
        showLoadingState(true);
        displayFormErrors({});

        const formData = {
            ingredient_name: document.getElementById('ingredient_name').value,
            source: document.getElementById('source').value,
            price: document.getElementById('price').value,
            quantity: document.getElementById('quantity').value,
            unit: document.getElementById('unit').value,
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
