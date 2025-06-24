// app/static/js/recipe_detail.js

// 注意：initialState 和 recipeId 必須由 HTML 模板通過 Jinja 渲染為全局變數，以便此 JS 檔案可以訪問。
// 例如在 recipe_detail.html 的 <script> 區塊中：
// <script>
//     const initialState = {{ initial_state | tojson }};
//     const recipeId = {{ recipe.id }};
// </script>

document.addEventListener('DOMContentLoaded', function() {
    // 確保這些變數在 HTML 模板中已定義並被此 JS 文件訪問
    const recipeState = initialState; 
    const recipeNameInput = document.getElementById('recipe-name-input');
    const servingWeightInput = document.getElementById('serving-weight');
    const servingsCountInput = document.getElementById('servings-count');
    const finalWeightInput = document.getElementById('final-weight');
    const searchBox = document.getElementById('ingredient-search-box');
    const sourceFilter = document.getElementById('source-filter');
    const searchResultsDiv = document.getElementById('search-results');
    const ingredientsTableBody = document.querySelector('#ingredients-table tbody');
    const noIngredientsMsg = document.getElementById('no-ingredients-msg');
    const saveButton = document.getElementById('save-recipe-btn');
    const printPreviewButton = document.getElementById('print-preview-btn');
    const totalWeightDiv = document.getElementById('total-weight-display');
    const totalCostDiv = document.getElementById('total-cost-display');
    const labelOptionsContainer = document.getElementById('label-options-container');
    const addIngredientModal = new bootstrap.Modal(document.getElementById('add-ingredient-modal'));
    const modalFormContainer = document.getElementById('modal-form-container');
    const modalSaveButton = document.getElementById('modal-save-btn');

    // 模態框內的表單模板
    const formTemplate = `
        <div class="row mb-3">
            <label for="modal_food_name" class="col-sm-4 col-form-label">食材名稱:</label>
            <div class="col-sm-8">
                <input type="text" id="modal_food_name" class="form-control" required>
            </div>
        </div>
        <div class="row mb-3">
            <label for="modal_cost_per_unit" class="col-sm-4 col-form-label">成本 (每100g):</label>
            <div class="col-sm-8">
                <input type="number" id="modal_cost_per_unit" class="form-control" value="0" min="0" step="0.01">
            </div>
        </div>
        <div class="row mb-3">
            <label for="modal_unit_name" class="col-sm-4 col-form-label">單位名稱:</label>
            <div class="col-sm-8">
                <input type="text" id="modal_unit_name" class="form-control" value="g">
            </div>
        </div>
        <div class="row mb-3">
            <label for="modal_calories_kcal" class="col-sm-4 col-form-label">熱量 (大卡/100g):</label>
            <div class="col-sm-8">
                <input type="number" id="modal_calories_kcal" class="form-control" value="0" required min="0" step="0.01">
            </div>
        </div>
        <div class="row mb-3">
            <label for="modal_protein_g" class="col-sm-4 col-form-label">蛋白質 (克/100g):</label>
            <div class="col-sm-8">
                <input type="number" id="modal_protein_g" class="form-control" value="0" required min="0" step="0.01">
            </div>
        </div>
        <div class="row mb-3">
            <label for="modal_fat_g" class="col-sm-4 col-form-label">總脂肪 (克/100g):</label>
            <div class="col-sm-8">
                <input type="number" id="modal_fat_g" class="form-control" value="0" required min="0" step="0.01">
            </div>
        </div>
        <div class="row mb-3">
            <label for="modal_saturated_fat_g" class="col-sm-4 col-form-label">飽和脂肪 (克/100g):</label>
            <div class="col-sm-8">
                <input type="number" id="modal_saturated_fat_g" class="form-control" value="0" required min="0" step="0.01">
            </div>
        </div>
        <div class="row mb-3">
            <label for="modal_trans_fat_g" class="col-sm-4 col-form-label">反式脂肪 (克/100g):</label>
            <div class="col-sm-8">
                <input type="number" id="modal_trans_fat_g" class="form-control" value="0" required min="0" step="0.01">
            </div>
        </div>
        <div class="row mb-3">
            <label for="modal_carbohydrate_g" class="col-sm-4 col-form-label">總碳水化合物 (克/100g):</label>
            <div class="col-sm-8">
                <input type="number" id="modal_carbohydrate_g" class="form-control" value="0" required min="0" step="0.01">
            </div>
        </div>
        <div class="row mb-3">
            <label for="modal_sugar_g" class="col-sm-4 col-form-label">糖 (克/100g):</label>
            <div class="col-sm-8">
                <input type="number" id="modal_sugar_g" class="form-control" value="0" required min="0" step="0.01">
            </div>
        </div>
        <div class="row mb-3">
            <label for="modal_sodium_mg" class="col-sm-4 col-form-label">鈉 (毫克/100g):</label>
            <div class="col-sm-8">
                <input type="number" id="modal_sodium_mg" class="form-control" value="0" required min="0" step="0.1">
            </div>
        </div>
        {# 新增『新增價格』按鈕 #}
        <div class="row mb-3">
            <div class="col-sm-8 offset-sm-4">
                <button type="button" id="modal_add_price_btn" class="btn btn-outline-secondary btn-sm w-100">
                    <i class="bi bi-currency-dollar me-2"></i>新增價格 (跳轉至價格紀錄頁面)
                </button>
            </div>
        </div>
    `;

    function setupInputEventListeners(containerElement) {
        const inputs = containerElement.querySelectorAll('input[type="number"]');
        inputs.forEach(input => {
            if (input.dataset.eventsAttached) return;
            input.addEventListener('focus', function() { if (this.value === '0' || this.value === '0.0') { this.value = ''; } });
            input.addEventListener('blur', function() { if (this.value === '') { this.value = '0'; } });
            input.dataset.eventsAttached = true;
        });
    }

    function renderTable() {
        ingredientsTableBody.innerHTML = '';
        noIngredientsMsg.style.display = recipeState.ingredients.length > 0 ? 'none' : 'block';
        recipeState.ingredients.forEach(item => {
            const newRow = document.createElement('tr');
            newRow.setAttribute('data-ingredient-id', item.ingredient_id);
            newRow.innerHTML = `
                <td>${item.ingredient_name}</td>
                <td class="text-end"><input type="number" class="form-control form-control-sm text-end weight-input" value="${item.quantity_g}" min="0" step="0.1" data-ingredient-id="${item.ingredient_id}"></td>
                <td>
                    <button class="btn btn-sm btn-outline-info arrow-btn up-btn" title="上移"><i class="bi bi-arrow-up-circle-fill"></i></button>
                    <button class="btn btn-sm btn-outline-info arrow-btn down-btn" title="下移"><i class="bi bi-arrow-down-circle-fill"></i></button>
                    <button class="btn btn-sm btn-outline-danger remove-btn" data-ingredient-id="${item.ingredient_id}" title="移除"><i class="bi bi-x-circle-fill"></i></button>
                </td>
            `;
            ingredientsTableBody.appendChild(newRow);
        });
        setupInputEventListeners(ingredientsTableBody);
    }

    function calculateAndDisplayNutrition() {
        const previewDiv = document.getElementById('nutrition-preview');
        let rawTotals = {
            calories_kcal: 0, protein_g: 0, fat_g: 0, carbohydrate_g: 0,
            saturated_fat_g: 0, trans_fat_g: 0, sugar_g: 0, sodium_mg: 0,
            total_weight_g: 0, total_cost: 0
        };
        recipeState.ingredients.forEach(item => {
            const quantity = parseFloat(item.quantity_g) || 0;
            if (quantity <= 0 || !item.details) return;
            const scale = quantity / 100.0;
            rawTotals.calories_kcal += (item.details.calories_kcal || 0) * scale;
            rawTotals.protein_g += (item.details.protein_g || 0) * scale;
            rawTotals.fat_g += (item.details.fat_g || 0) * scale;
            rawTotals.carbohydrate_g += (item.details.carbohydrate_g || 0) * scale;
            rawTotals.saturated_fat_g += (item.details.saturated_fat_g || 0) * scale;
            rawTotals.trans_fat_g += (item.details.trans_fat_g || 0) * scale;
            rawTotals.sugar_g += (item.details.sugar_g || 0) * scale;
            rawTotals.sodium_mg += (item.details.sodium_mg || 0) * scale;
            rawTotals.total_weight_g += quantity;
            rawTotals.total_cost += ((item.details.cost_per_unit || 0) / 100.0) * quantity;
        });

        totalWeightDiv.innerHTML = `<strong>原料總重: ${rawTotals.total_weight_g.toFixed(1)} 公克</strong>`;
        totalCostDiv.innerHTML = `<strong>食譜總成本: NT$ ${rawTotals.total_cost.toFixed(2)}</strong>`;

        const finalWeight = parseFloat(finalWeightInput.value) || rawTotals.total_weight_g;
        const servingsCount = parseInt(servingsCountInput.value) || 1;
        const servingWeight = (finalWeight > 0 && servingsCount > 0) ? (finalWeight / servingsCount) : 0;
        if (finalWeight <= 0) {
            previewDiv.innerHTML = '<div class="alert alert-info text-center mt-3"><h2>營養標示 (預覽)</h2><p>請先加入食材或設定烘焙後總重以計算營養成分。</p></div>';
            if(printPreviewButton) printPreviewButton.style.display = 'none';
            return;
        }
        if(printPreviewButton) printPreviewButton.style.display = 'block';
        const density = {};
        for (const key in rawTotals) {
            if (key !== 'total_cost' && finalWeight > 0) {
                density[key] = rawTotals[key] / finalWeight;
            } else if (key !== 'total_cost') {
                density[key] = 0;
            }
        }
        const perServing = {};
        const per100g = {};
        for (const key in density) {
            perServing[key] = density[key] * servingWeight;
            per100g[key] = density[key] * 100;
        }

        const showNutrients = recipeState.label_options.show_nutrients || {};
        let nutritionTableHtml = `
            <h2 class="text-center text-primary mb-3">營養標示</h2>
            <table class="nutrition-table table table-sm table-bordered">
                <thead>
                    <tr><td colspan="3" class="text-start">每一份量 ${servingWeight.toFixed(1)} 公克</td></tr>
                    <tr><td colspan="3" class="text-start" style="border-bottom: 2px solid black;">本包裝含 ${servings_count} 份</td></tr>
                    <tr class="header-row"><th></th><th class="text-end">每份</th><th class="text-end">每100公克</th></tr>
                </thead>
                <tbody>
        `;

        const nutrientOrder = [
            'calories_kcal', 'protein_g', 'fat_g', 'saturated_fat_g', 'trans_fat_g',
            'carbohydrate_g', 'sugar_g', 'sodium_mg'
        ];
        const nutrientNames = {
            'calories_kcal': '熱量',
            'protein_g': '蛋白質',
            'fat_g': '脂肪',
            'saturated_fat_g': '飽和脂肪',
            'trans_fat_g': '反式脂肪',
            'carbohydrate_g': '碳水化合物',
            'sugar_g': '糖',
            'sodium_mg': '鈉'
        };
        const indentNutrients = ['saturated_fat_g', 'trans_fat_g', 'sugar_g'];

        nutrientOrder.forEach((key, index) => {
            if (showNutrients[key] !== false && (perServing[key] !== undefined && per100g[key] !== undefined)) { 
                const isIndented = indentNutrients.includes(key) ? 'nutrient-name-indent' : '';
                const noBorderBottomClass = (index === nutrientOrder.length - 1) ? 'no-border-bottom' : '';
                const unit = (key === 'calories_kcal') ? '大卡' : (key === 'sodium_mg' ? '毫克' : '公克');
                const fixed = (key === 'sodium_mg') ? 0 : 1;

                nutritionTableHtml += `
                    <tr class="${noBorderBottomClass}">
                        <th class="${isIndented}">${nutrientNames[key]}</th>
                        <td class="text-end">${perServing[key].toFixed(fixed)} ${unit}</td>
                        <td class="text-end">${per100g[key].toFixed(fixed)} ${unit}</td>
                    </tr>
                `;
            }
        });

        nutritionTableHtml += `</tbody></table>`;
        previewDiv.innerHTML = nutritionTableHtml;
    }
    
    function calculateServingWeight() {
        const finalWeight = parseFloat(finalWeightInput.value) || 0;
        const servingsCount = parseInt(servingsCountInput.value) || 1;
        servingWeightInput.value = (finalWeight > 0 && servingsCount > 0) ? (finalWeight / servingsCount).toFixed(1) : '0.0';
    }

    function updateAll() { renderTable(); calculateAndDisplayNutrition(); }

    function addIngredientToState(ingredientData) {
        if (recipeState.ingredients.some(item => item.ingredient_id == ingredientData.id)) { alert('這個食材已經在列表中了！'); return; }
        recipeState.ingredients.push({
            ingredient_id: ingredientData.id,
            ingredient_name: ingredientData.name,
            quantity_g: 0,
            details: {
                calories_kcal: ingredientData.calories_kcal, protein_g: ingredientData.protein_g,
                fat_g: ingredientData.fat_g, saturated_fat_g: ingredientData.saturated_fat_g,
                trans_fat_g: ingredientData.trans_fat_g, carbohydrate_g: ingredientData.carbohydrate_g,
                sugar_g: ingredientData.sugar_g, sodium_mg: ingredientData.sodium_mg,
                cost_per_unit: ingredientData.cost_per_unit,
                unit_name: ingredientData.unit_name
            }
        });
        updateAll();
    }
    
    function updateStateOrder() {
        const newOrder = [];
        const rows = ingredientsTableBody.querySelectorAll('tr');
        rows.forEach(row => {
            const ingredientId = parseInt(row.getAttribute('data-ingredient-id'));
            const item = recipeState.ingredients.find(i => i.ingredient_id === ingredientId);
            if (item) {
                const newQuantity = parseFloat(row.querySelector('.weight-input').value) || 0;
                item.quantity_g = newQuantity;
                newOrder.push(item);
            }
        });
        recipeState.ingredients = newOrder;
        calculateAndDisplayNutrition();
    }

    function performSearch() {
        const query = searchBox.value.trim();
        const source = sourceFilter.value;
        if (!query && source === 'ALL') { searchResultsDiv.innerHTML = '<p class="text-muted p-2 text-center">請輸入關鍵字搜尋。</p>'; return; }
        fetch(`/recipes/api/search_ingredients?q=${query}&source=${source}`)
            .then(response => response.json())
            .then(data => {
                searchResultsDiv.innerHTML = '';
                if (data.length > 0) {
                    data.forEach(ingredient => {
                        const resultItem = document.createElement('div');
                        resultItem.textContent = ingredient.name;
                        resultItem.className = 'list-group-item list-group-item-action';
                        resultItem.addEventListener('click', () => addIngredientToState(ingredient));
                        searchResultsDiv.appendChild(resultItem);
                    });
                } else if (query) {
                    const createBtn = document.createElement('button');
                    createBtn.textContent = `+ 新增「${query}」為自訂食材`;
                    createBtn.className = 'btn btn-info mt-3 w-100';
                    createBtn.addEventListener('click', () => openAddModal(query));
                    searchResultsDiv.appendChild(createBtn);
                } else {
                    searchResultsDiv.innerHTML = '<p class="text-muted p-2 text-center">沒有找到符合條件的食材。</p>';
                }
            })
            .catch(error => {
                console.error('Error searching ingredients:', error);
                searchResultsDiv.innerHTML = '<p class="text-danger p-2 text-center">搜尋食材時發生錯誤。</p>';
            });
    }

    function openAddModal(prefilledName) {
        modalFormContainer.innerHTML = formTemplate;
        document.getElementById('modal_food_name').value = prefilledName;
        addIngredientModal.show();
        setupInputEventListeners(modalFormContainer);
        setupModalPriceButton();
    }

    function setupModalPriceButton() {
        const addPriceBtn = document.getElementById('modal_add_price_btn');
        if (addPriceBtn) {
            addPriceBtn.addEventListener('click', function() {
                const ingredientName = document.getElementById('modal_food_name').value;
                if (!ingredientName) {
                    alert('請先輸入食材名稱才能新增價格。');
                    return;
                }
                window.open("{{ url_for('pricing.add_price') }}?ingredient_name=" + encodeURIComponent(ingredientName), '_blank');
            });
        }
    }


    function initializePage() {
        servingWeightInput.value = recipeState.serving_weight_g;
        servingsCountInput.value = recipeState.servings_count;
        finalWeightInput.value = recipeState.final_weight_g || '';
        if (recipeState.label_options) {
            const savedNutrients = recipeState.label_options.show_nutrients || {};
            const savedAllergens = recipeState.label_options.allergens || [];
            labelOptionsContainer.querySelectorAll('.label-option-nutrient').forEach(checkbox => {
                checkbox.checked = savedNutrients[checkbox.value] !== false;
                checkbox.id = `nutrient-${checkbox.value}`;
                checkbox.nextElementSibling.setAttribute('for', `nutrient-${checkbox.value}`);
            });
            labelOptionsContainer.querySelectorAll('.allergen-option').forEach(checkbox => {
                checkbox.checked = savedAllergens.includes(checkbox.value);
                checkbox.id = `allergen-${checkbox.value}`;
                checkbox.nextElementSibling.setAttribute('for', `allergen-${checkbox.value}`);
            });
        } else {
             labelOptionsContainer.querySelectorAll('input[type="checkbox"]').forEach(checkbox => { checkbox.checked = true; });
        }
        updateAll();
        performSearch();
        calculateServingWeight();
    }
    
    ingredientsTableBody.addEventListener('input', function(event) { if (event.target.classList.contains('weight-input')) { const ingredientIdToUpdate = parseInt(event.target.getAttribute('data-ingredient-id')); const newQuantity = parseFloat(event.target.value) || 0; const item = recipeState.ingredients.find(i => i.ingredient_id == ingredientIdToUpdate); if(item) { item.quantity_g = newQuantity; } calculateAndDisplayNutrition(); } });
    ingredientsTableBody.addEventListener('click', function(event) {
        const target = event.target;
        const button = target.closest('button'); 

        if (!button) return;

        if (button.classList.contains('remove-btn')) {
            const ingredientIdToRemove = parseInt(button.getAttribute('data-ingredient-id'));
            if (confirm(`您確定要移除嗎？`)) { recipeState.ingredients = recipeState.ingredients.filter(item => item.ingredient_id != ingredientIdToRemove); updateAll(); }
        } else if (button.classList.contains('up-btn')) {
            const row = button.closest('tr');
            const prevRow = row.previousElementSibling;
            if (prevRow) { ingredientsTableBody.insertBefore(row, prevRow); updateStateOrder(); }
        } else if (button.classList.contains('down-btn')) {
            const row = button.closest('tr');
            const nextRow = row.nextElementSibling;
            if (nextRow) { ingredientsTableBody.insertBefore(nextRow, row); updateStateOrder(); }
        }
    });

    saveButton.addEventListener('click', function() {
        updateStateFromUI();
        saveButton.disabled = true;
        saveButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>儲存中...';

        fetch(`/recipes/api/recipe/${recipeId}/save`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(recipeState) })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                if (data.status === 'success') {
                    window.location.reload();
                }
            })
            .catch(error => {
                console.error('Error saving recipe:', error);
                alert('儲存食譜時發生錯誤。');
            })
            .finally(() => {
                saveButton.disabled = false;
                saveButton.innerHTML = '<i class="bi bi-save me-2"></i>儲存食譜';
            });
    });

    function updateStateFromUI() {
        recipeState.recipe_name = recipeNameInput.value;
        recipeState.serving_weight_g = parseFloat(servingWeightInput.value) || 100;
        recipeState.servings_count = parseInt(servingsCountInput.value) || 1;
        recipeState.final_weight_g = parseFloat(finalWeightInput.value) || null;
        
        const showNutrients = {};
        labelOptionsContainer.querySelectorAll('.label-option-nutrient').forEach(checkbox => { showNutrients[checkbox.value] = checkbox.checked; });
        const allergens = [];
        labelOptionsContainer.querySelectorAll('.allergen-option:checked').forEach(checkbox => { allergens.push(checkbox.value); });
        recipeState.label_options = { show_nutrients: showNutrients, allergens: allergens };

        const itemsInTable = [];
        const rows = ingredientsTableBody.querySelectorAll('tr');
        rows.forEach(row => {
            const id = parseInt(row.getAttribute('data-ingredient-id'));
            const originalItem = recipeState.ingredients.find(i => i.ingredient_id === id);
            if (originalItem) {
                originalItem.quantity_g = parseFloat(row.querySelector('.weight-input').value) || 0;
                itemsInTable.push(originalItem);
            }
        });
        recipeState.ingredients = itemsInTable;
    }

    modalSaveButton.addEventListener('click', function() {
        const formData = {
            food_name: document.getElementById('modal_food_name').value,
            cost_per_unit: document.getElementById('modal_cost_per_unit').value || 0,
            unit_name: document.getElementById('modal_unit_name').value || 'g', 
            calories_kcal: document.getElementById('modal_calories_kcal').value,
            protein_g: document.getElementById('modal_protein_g').value,
            fat_g: document.getElementById('modal_fat_g').value,
            saturated_fat_g: document.getElementById('modal_saturated_fat_g').value,
            trans_fat_g: document.getElementById('modal_trans_fat_g').value,
            carbohydrate_g: document.getElementById('modal_carbohydrate_g').value,
            sugar_g: document.getElementById('modal_sugar_g').value,
            sodium_mg: document.getElementById('modal_sodium_mg').value,
        };
        modalSaveButton.disabled = true;
        modalSaveButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>儲存中...';

        fetch('/recipes/api/ingredient/create', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(formData) })
        .then(response => response.json()).then(result => {
            alert(`「${result.ingredient.name}」已成功新增！`);
            if (result.status === 'success') {
                addIngredientModal.hide();
                const newIngredientData = {
                    id: result.ingredient.id, name: result.ingredient.name,
                    calories_kcal: parseFloat(formData.calories_kcal), protein_g: parseFloat(formData.protein_g),
                    fat_g: parseFloat(formData.fat_g), saturated_fat_g: parseFloat(formData.saturated_fat_g),
                    trans_fat_g: parseFloat(formData.trans_fat_g), carbohydrate_g: parseFloat(formData.carbohydrate_g),
                    sugar_g: parseFloat(formData.sugar_g), sodium_mg: parseFloat(formData.sodium_mg),
                    cost_per_unit: parseFloat(formData.cost_per_unit),
                    unit_name: formData.unit_name
                };
                addIngredientToState(newIngredientData);
                searchBox.value = '';
                performSearch();
            } else { alert(`新增失敗: ${result.message}`); }
        })
        .catch(error => {
            console.error('Error saving modal ingredient:', error);
            alert('儲存新食材時發生錯誤。');
        })
        .finally(() => {
            modalSaveButton.disabled = false;
            modalSaveButton.innerHTML = '儲存新食材';
        });
    });

    let searchTimeoutGlobal;
    searchBox.addEventListener('keyup', function(e){ clearTimeout(searchTimeoutGlobal); searchTimeoutGlobal = setTimeout(() => performSearch(), 300) });
    sourceFilter.addEventListener('change', performSearch);
    finalWeightInput.addEventListener('input', () => { calculateServingWeight(); calculateAndDisplayNutrition(); });
    servingsCountInput.addEventListener('input', () => { calculateServingWeight(); calculateAndDisplayNutrition(); });
    
    labelOptionsContainer.querySelectorAll('.label-option-nutrient').forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            const nutrientName = checkbox.value;
            recipeState.label_options = recipeState.label_options || {};
            recipeState.label_options.show_nutrients = recipeState.label_options.show_nutrients || {};
            recipeState.label_options.show_nutrients[nutrientName] = checkbox.checked;
            calculateAndDisplayNutrition();
        });
    });

    labelOptionsContainer.querySelectorAll('.allergen-option').forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            const allergenName = checkbox.value;
            recipeState.label_options = recipeState.label_options || {};
            recipeState.label_options.allergens = recipeState.label_options.allergens || [];
            if (checkbox.checked) {
                if (!recipeState.label_options.allergens.includes(allergenName)) {
                    recipeState.label_options.allergens.push(allergenName);
                }
            } else {
                recipeState.label_options.allergens = recipeState.label_options.allergens.filter(a => a !== allergenName);
            }
        });
    });

    initializePage();
});