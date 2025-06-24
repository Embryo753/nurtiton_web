// app/static/js/manage_ingredients.js

document.addEventListener('DOMContentLoaded', function() {
    const formTemplate = `
        <div class="row mb-3 form-row-compact">
            <label for="food_name" class="col-sm-4 col-form-label">食材名稱:</label>
            <div class="col-sm-8">
                <input type="text" id="food_name" name="food_name" class="form-control" required>
                <div class="invalid-feedback" id="error-food_name"></div>
            </div>
        </div>
        <div class="row mb-3 form-row-compact">
            <label for="cost_per_unit" class="col-sm-4 col-form-label">成本 (每100g):</label>
            <div class="col-sm-8">
                <input type="number" id="cost_per_unit" name="cost_per_unit" class="form-control" value="0" required min="0" step="0.01">
                <div class="invalid-feedback" id="error-cost_per_unit"></div>
            </div>
        </div>
        <div class="row mb-3 form-row-compact">
            <label for="unit_name" class="col-sm-4 col-form-label">單位名稱:</label>
            <div class="col-sm-8">
                <input type="text" id="unit_name" name="unit_name" class="form-control" value="g" required>
                <div class="invalid-feedback" id="error-unit_name"></div>
            </div>
        </div>
        <div class="row mb-3 form-row-compact">
            <label for="calories_kcal" class="col-sm-4 col-form-label">熱量 (大卡/100g):</label>
            <div class="col-sm-8">
                <input type="number" id="calories_kcal" name="calories_kcal" class="form-control" value="0" required min="0" step="0.01">
                <div class="invalid-feedback" id="error-calories_kcal"></div>
            </div>
        </div>
        <div class="row mb-3 form-row-compact">
            <label for="protein_g" class="col-sm-4 col-form-label">蛋白質 (克/100g):</label>
            <div class="col-sm-8">
                <input type="number" id="protein_g" name="protein_g" class="form-control" value="0" required min="0" step="0.01">
                <div class="invalid-feedback" id="error-protein_g"></div>
            </div>
        </div>
        <div class="row mb-3 form-row-compact">
            <label for="fat_g" class="col-sm-4 col-form-label">總脂肪 (克/100g):</label>
            <div class="col-sm-8">
                <input type="number" id="fat_g" name="fat_g" class="form-control" value="0" required min="0" step="0.01">
                <div class="invalid-feedback" id="error-fat_g"></div>
            </div>
        </div>
        <div class="row mb-3 form-row-compact">
            <label for="saturated_fat_g" class="col-sm-4 col-form-label">飽和脂肪 (克/100g):</label>
            <div class="col-sm-8">
                <input type="number" id="saturated_fat_g" name="saturated_fat_g" class="form-control" value="0" required min="0" step="0.01">
                <div class="invalid-feedback" id="error-saturated_fat_g"></div>
            </div>
        </div>
        <div class="row mb-3 form-row-compact">
            <label for="trans_fat_g" class="col-sm-4 col-form-label">反式脂肪 (克/100g):</label>
            <div class="col-sm-8">
                <input type="number" id="trans_fat_g" name="trans_fat_g" class="form-control" value="0" required min="0" step="0.01">
                <div class="invalid-feedback" id="error-trans_fat_g"></div>
            </div>
        </div>
        <div class="row mb-3 form-row-compact">
            <label for="carbohydrate_g" class="col-sm-4 col-form-label">總碳水化合物 (克/100g):</label>
            <div class="col-sm-8">
                <input type="number" id="carbohydrate_g" name="carbohydrate_g" class="form-control" value="0" required min="0" step="0.01">
                <div class="invalid-feedback" id="error-carbohydrate_g"></div>
            </div>
        </div>
        <div class="row mb-3 form-row-compact">
            <label for="sugar_g" class="col-sm-4 col-form-label">糖 (克/100g):</label>
            <div class="col-sm-8">
                <input type="number" id="sugar_g" name="sugar_g" class="form-control" value="0" required min="0" step="0.01">
                <div class="invalid-feedback" id="error-sugar_g"></div>
            </div>
        </div>
        <div class="row mb-3 form-row-compact">
            <label for="sodium_mg" class="col-sm-4 col-form-label">鈉 (毫克/100g):</label>
            <div class="col-sm-8">
                <input type="number" id="sodium_mg" name="sodium_mg" class="form-control" value="0" required min="0" step="0.1">
                <div class="invalid-feedback" id="error-sodium_mg"></div>
            </div>
        </div>
    `;

    const searchBox = document.getElementById('ingredient-search-box');
    const searchResultsDiv = document.getElementById('search-results');
    const formContainer = document.getElementById('ingredient-form');
    const formTitle = document.getElementById('form-title');
    const newButton = document.getElementById('new-btn');
    const saveButton = document.getElementById('save-btn');
    const deleteButton = document.getElementById('delete-btn');
    const cancelButton = document.getElementById('cancel-btn');
    
    const saveButtonText = document.getElementById('save-button-text');
    const saveSpinner = document.getElementById('save-spinner');
    const deleteButtonText = document.getElementById('delete-button-text');
    const deleteSpinner = document.getElementById('delete-spinner');

    let currentIngredientId = null;

    function showLoadingState(buttonId, isLoading) {
        const button = document.getElementById(buttonId);
        const textSpan = button.querySelector('span:not(.spinner-border)');
        const spinner = button.querySelector('.spinner-border');

        if (isLoading) {
            button.disabled = true;
            if (textSpan) textSpan.classList.add('d-none');
            if (spinner) spinner.classList.remove('d-none');
        } else {
            button.disabled = false;
            if (textSpan) textSpan.classList.remove('d-none');
            if (spinner) spinner.classList.add('d-none');
        }
    }

    function displayFormErrors(errors) {
        // 清除所有舊的錯誤訊息和無效狀態
        document.querySelectorAll('.form-control.is-invalid').forEach(el => el.classList.remove('is-invalid'));
        document.querySelectorAll('.form-select.is-invalid').forEach(el => el.classList.remove('is-invalid'));
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

    function setupFormEventListeners() {
        const inputs = formContainer.querySelectorAll('input[type="number"]');
        inputs.forEach(input => {
            input.addEventListener('focus', function() {
                if (this.value === '0') {
                    this.value = '';
                }
            });
            input.addEventListener('blur', function() {
                if (this.value === '') {
                    this.value = '0';
                }
            });
        });

        // 實時清除錯誤
        formContainer.querySelectorAll('.form-control').forEach(input => {
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
    }

    function getFormData() {
        return {
            food_name: document.getElementById('food_name').value,
            cost_per_unit: document.getElementById('cost_per_unit').value,
            unit_name: document.getElementById('unit_name').value,
            calories_kcal: document.getElementById('calories_kcal').value,
            protein_g: document.getElementById('protein_g').value,
            fat_g: document.getElementById('fat_g').value,
            saturated_fat_g: document.getElementById('saturated_fat_g').value,
            trans_fat_g: document.getElementById('trans_fat_g').value,
            carbohydrate_g: document.getElementById('carbohydrate_g').value,
            sugar_g: document.getElementById('sugar_g').value,
            sodium_mg: document.getElementById('sodium_mg').value,
        };
    }

    function performSearch() {
        const query = searchBox.value;
        fetch(`/recipes/api/search_ingredients?q=${query}&source=USER`)
            .then(response => response.json())
            .then(data => {
                searchResultsDiv.innerHTML = '';
                if (data.length > 0) {
                    data.forEach(ingredient => {
                        const itemDiv = document.createElement('div');
                        itemDiv.textContent = ingredient.name;
                        itemDiv.className = 'list-group-item list-group-item-action';
                        itemDiv.setAttribute('data-id', ingredient.id);
                        if (ingredient.id == currentIngredientId) { itemDiv.classList.add('active'); }
                        itemDiv.addEventListener('click', () => selectIngredient(ingredient.id));
                        searchResultsDiv.appendChild(itemDiv);
                    });
                } else {
                    searchResultsDiv.innerHTML = '<p class="text-muted p-2 text-center">沒有找到符合條件的食材。</p>';
                }
            })
            .catch(error => {
                console.error('Error searching ingredients:', error);
                searchResultsDiv.innerHTML = '<p class="text-danger p-2 text-center">搜尋食材時發生錯誤。</p>';
            });
    }

    function selectIngredient(ingredientId) {
        fetch(`/recipes/api/ingredient/${ingredientId}`)
            .then(response => response.json())
            .then(result => {
                if (result.status === 'success') {
                    formContainer.innerHTML = formTemplate;
                    const data = result.data;
                    currentIngredientId = data.id;
                    formTitle.textContent = `編輯: ${data.food_name}`;
                    
                    document.getElementById('food_name').value = data.food_name;
                    document.getElementById('cost_per_unit').value = data.cost_per_unit;
                    document.getElementById('unit_name').value = data.unit_name;
                    document.getElementById('calories_kcal').value = data.calories_kcal;
                    document.getElementById('protein_g').value = data.protein_g;
                    document.getElementById('fat_g').value = data.fat_g;
                    document.getElementById('saturated_fat_g').value = data.saturated_fat_g;
                    document.getElementById('trans_fat_g').value = data.trans_fat_g;
                    document.getElementById('carbohydrate_g').value = data.carbohydrate_g;
                    document.getElementById('sugar_g').value = data.sugar_g;
                    document.getElementById('sodium_mg').value = data.sodium_mg;

                    newButton.disabled = false;
                    showLoadingState('save-btn', false);
                    showLoadingState('delete-btn', false);
                    cancelButton.disabled = false;
                    document.querySelectorAll('.list-group-item').forEach(el => el.classList.remove('active'));
                    document.querySelector(`.list-group-item[data-id="${ingredientId}"]`).classList.add('active');
                    setupFormEventListeners();
                    displayFormErrors({});
                } else {
                    alert('獲取食材詳情失敗: ' + result.message);
                }
            })
            .catch(error => {
                console.error('Error fetching ingredient details:', error);
                alert('獲取食材詳情時發生錯誤。');
            });
    }


    function resetToInitialState() {
        formContainer.innerHTML = '<p class="alert alert-info text-center"><i>請從左側列表選擇一個食材來編輯，或點擊右側的「新增」按鈕。</i></p>';
        formTitle.textContent = '編輯食材資料';
        newButton.disabled = false;
        saveButton.disabled = true;
        deleteButton.disabled = true;
        cancelButton.disabled = true;
        currentIngredientId = null;
        document.querySelectorAll('.list-group-item').forEach(el => el.classList.remove('active'));
        displayFormErrors({});
    }

    newButton.addEventListener('click', function() {
        formContainer.innerHTML = formTemplate;
        formTitle.textContent = '新增食材';
        currentIngredientId = 'new';
        newButton.disabled = true;
        showLoadingState('save-btn', false);
        deleteButton.disabled = true;
        cancelButton.disabled = false;
        document.querySelectorAll('.list-group-item').forEach(el => el.classList.remove('active'));
        setupFormEventListeners();
        displayFormErrors({});
    });

    cancelButton.addEventListener('click', function() {
        resetToInitialState();
        performSearch();
    });

    saveButton.addEventListener('click', function() {
        const formData = getFormData();
        let url;
        if (currentIngredientId === 'new') {
            url = `/recipes/api/ingredient/create`;
        } else {
            url = `/recipes/api/ingredient/${currentIngredientId}/update`;
        }
        
        showLoadingState('save-btn', true);
        displayFormErrors({});

        fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(formData) })
        .then(response => response.json())
        .then(result => {
            alert(result.message);
            if (result.status === 'success') {
                performSearch();
                resetToInitialState();
            } else if (result.errors) {
                displayFormErrors(result.errors);
            }
        })
        .catch(error => {
            console.error('Error saving ingredient:', error);
            alert('儲存食材時發生錯誤。');
        })
        .finally(() => {
            showLoadingState('save-btn', false);
        });
    });

    deleteButton.addEventListener('click', function() {
        if (currentIngredientId && currentIngredientId !== 'new' && confirm('您確定要永久刪除這個食材嗎？此操作無法恢復！')) {
            showLoadingState('delete-btn', true);

            fetch(`/recipes/api/ingredient/${currentIngredientId}/delete`, { method: 'POST' })
            .then(response => response.json())
            .then(result => {
                alert(result.message);
                if (result.status === 'success') {
                    performSearch();
                    resetToInitialState();
                }
            })
            .catch(error => {
                console.error('Error deleting ingredient:', error);
                alert('刪除食材時發生錯誤。');
            })
            .finally(() => {
                showLoadingState('delete-btn', false);
            });
        }
    });

    searchBox.addEventListener('keyup', performSearch);
    resetToInitialState();
    performSearch();
});