// app/static/js/products.js
document.addEventListener('DOMContentLoaded', function() {
    // --- DOM 元素 (保持不變) ---
    const productSearchBox = document.getElementById('product-search-box');
    const productListDiv = document.getElementById('product-list');
    const formContainer = document.getElementById('product-form');
    const formTitle = document.getElementById('form-title');
    const newButton = document.getElementById('new-btn');
    const saveButton = document.getElementById('save-btn');
    const deleteButton = document.getElementById('delete-btn');
    const cancelButton = document.getElementById('cancel-btn');
    const createProductModal = new bootstrap.Modal(document.getElementById('create-product-modal'));
    const recipeSearchBox = document.getElementById('recipe-search-box');
    const recipeSearchResultsDiv = document.getElementById('recipe-search-results');

    // --- 狀態管理 ---
    let currentProductId = null;
    let selectedRecipeDataForCreation = null;

    // --- 從 HTML 傳遞的後端資料 (保持不變) ---
    const allProductsInitialData = window.allProductsInitialData || [];
    const allRecipesInitialData = window.allRecipesInitialData || [];
    const electricityCostPerKwh = window.electricityCostPerKwh || 0;
    const laborCostPerHour = window.laborCostPerHour || 0;

    // --- 函式：更新按鈕狀態 (保持不變) ---
    function updateButtonStates() {
        saveButton.disabled = !(currentProductId === 'new' || typeof currentProductId === 'number');
        cancelButton.disabled = !(currentProductId === 'new' || typeof currentProductId === 'number');
        deleteButton.disabled = !(typeof currentProductId === 'number');
        newButton.disabled = (currentProductId === 'new' || typeof currentProductId === 'number');
    }

    // --- 函式：重設表單和狀態 (保持不變) ---
    function resetToInitialState() {
        currentProductId = null;
        selectedRecipeDataForCreation = null;
        formContainer.innerHTML = '<p class="alert alert-info text-center"><i>請從左側列表選擇一個產品來編輯，或點擊右側的「新增」按鈕。</i></p>';
        formTitle.textContent = '產品資料';
        document.querySelectorAll('.list-group-item.active').forEach(el => el.classList.remove('active'));
        updateButtonStates();
    }
    
    // --- ★ 主要修改處：渲染產品表單的函數 ---
    function renderProductForm(productData) {
        // `productData` 現在應該包含 recipe_details 和其中的 ingredient_cost_details
        const recipeDetails = productData.recipe_details || {};
        const ingredientCostDetails = recipeDetails.ingredient_cost_details || [];

        // 建立食材成本細項表格的 HTML
        let ingredientsTableHTML = `
            <table class="table table-sm table-bordered cost-table">
                <thead>
                    <tr>
                        <th>食材名稱</th>
                        <th class="text-end">用量 (克)</th>
                        <th class="text-end">每克成本</th>
                        <th>來源</th>
                        <th class="text-end">單項成本</th>
                    </tr>
                </thead>
                <tbody>
        `;
        if (ingredientCostDetails.length > 0) {
            ingredientCostDetails.forEach(item => {
                ingredientsTableHTML += `
                    <tr>
                        <td>${item.ingredient_name}</td>
                        <td class="text-end">${item.quantity_g.toFixed(1)}</td>
                        <td class="text-end">${item.cost_per_gram.toFixed(4)}</td>
                        <td><small>${item.cost_source || '無'}</small></td>
                        <td class="text-end">${item.item_total_cost.toFixed(2)}</td>
                    </tr>
                `;
            });
        } else {
            ingredientsTableHTML += `<tr><td colspan="5" class="text-muted text-center">此食譜沒有成本細項。</td></tr>`;
        }
        ingredientsTableHTML += `
                </tbody>
                <tfoot>
                    <tr>
                        <th colspan="4" class="text-end">食譜食材總成本:</th>
                        <th class="text-end" id="total-ingredient-cost-display">NT$ ${recipeDetails.total_ingredient_cost ? recipeDetails.total_ingredient_cost.toFixed(2) : '0.00'}</th>
                    </tr>
                </tfoot>
            </table>
        `;

        // 建立完整的表單 HTML
        const formHTML = `
            <input type="hidden" id="recipe_id" value="${productData.recipe_id || ''}">
            <h4 class="form-section-title">產品基本資訊</h4>
            <div class="mb-3">
                <label for="product_name" class="form-label">產品名稱</label>
                <input type="text" id="product_name" class="form-control" value="${productData.product_name || ''}">
            </div>
            <div class="mb-3">
                <label for="description" class="form-label">產品描述</label>
                <textarea id="description" class="form-control" rows="2">${productData.description || ''}</textarea>
            </div>
            
            <!-- 食材成本細項表格注入點 -->
            <h4 class="form-section-title">食材成本細項 (基於食譜)</h4>
            ${ingredientsTableHTML}

            <h4 class="form-section-title">生產參數</h4>
            <div class="row">
                <div class="col-md-6 mb-3"><label for="batch_size" class="form-label">一次烤焙份數</label><input type="number" id="batch_size" class="form-control" value="${productData.batch_size || recipeDetails.servings_count || 1}" min="1"></div>
                <div class="col-md-6 mb-3"><label for="production_time_hr" class="form-label">單次製作時間 (小時)</label><input type="number" id="production_time_hr" class="form-control" value="${productData.production_time_hr || 0}" min="0" step="0.1"></div>
                <div class="col-md-6 mb-3"><label for="bake_power_w" class="form-label">烤箱功率 (瓦特)</label><input type="number" id="bake_power_w" class="form-control" value="${productData.bake_power_w || 0}" min="0"></div>
                <div class="col-md-6 mb-3"><label for="bake_time_min" class="form-label">烤焙時間 (分鐘)</label><input type="number" id="bake_time_min" class="form-control" value="${productData.bake_time_min || 0}" min="0"></div>
            </div>

            <h4 class="form-section-title">總成本預覽 (每批次)</h4>
            <div id="cost-preview-section" class="p-3 bg-light rounded shadow-sm mb-3">
                <p class="mb-1">批次食材總成本: <strong id="batch-ingredient-total-cost">NT$ 0.00</strong></p>
                <p class="mb-1">電費成本: <strong id="electricity-cost">NT$ 0.00</strong></p>
                <p class="mb-1">人力成本: <strong id="labor-cost">NT$ 0.00</strong></p>
                <p class="mb-1">批次總成本: <strong id="total-batch-cost">NT$ 0.00</strong></p>
                <p class="fs-5 text-success mt-2">平均每個產品總成本: <strong id="avg-cost-per-product">NT$ 0.00</strong></p>
            </div>
            
            <h4 class="form-section-title">產品定價與庫存</h4>
            <div class="row">
                <div class="col-md-6 mb-3"><label for="selling_price" class="form-label">銷售價格</label><input type="number" id="selling_price" class="form-control" value="${productData.selling_price || 0}" min="0"></div>
                <div class="col-md-6 mb-3"><label for="stock_quantity" class="form-label">庫存數量</label><input type="number" id="stock_quantity" class="form-control" value="${productData.stock_quantity || 0}" min="0"></div>
            </div>
        `;
        formContainer.innerHTML = formHTML;
        calculateAndDisplayCosts();
        ['batch_size', 'production_time_hr', 'bake_power_w', 'bake_time_min'].forEach(id => {
            document.getElementById(id).addEventListener('input', calculateAndDisplayCosts);
        });
    }

    // --- ★ 修改處：計算並顯示成本的函數 ---
    function calculateAndDisplayCosts() {
        const recipeData = selectedRecipeDataForCreation;
        if (!recipeData || !recipeData.total_ingredient_cost) return;
        
        const batchSize = parseFloat(document.getElementById('batch_size').value) || 1;
        const bakePowerW = parseFloat(document.getElementById('bake_power_w').value) || 0;
        const bakeTimeMin = parseFloat(document.getElementById('bake_time_min').value) || 0;
        const productionTimeHr = parseFloat(document.getElementById('production_time_hr').value) || 0;

        // 這裡的計算邏輯需要和後端 product.calculate_total_product_cost() 保持一致
        const ingredientCostPerServing = recipeData.total_ingredient_cost / (recipeData.servings_count || 1);
        const batchIngredientTotalCost = ingredientCostPerServing * batchSize;
        
        const totalBakeTimeHr = bakeTimeMin / 60.0;
        const totalElectricityKwh = (bakePowerW * totalBakeTimeHr) / 1000.0;
        const electricityCost = totalElectricityKwh * electricityCostPerKwh;
        
        const laborCost = productionTimeHr * laborCostPerHour;
        const totalBatchCost = batchIngredientTotalCost + electricityCost + laborCost;
        const avgCostPerProduct = batchSize > 0 ? totalBatchCost / batchSize : 0;

        document.getElementById('batch-ingredient-total-cost').textContent = `NT$ ${batchIngredientTotalCost.toFixed(2)}`;
        document.getElementById('electricity-cost').textContent = `NT$ ${electricityCost.toFixed(2)}`;
        document.getElementById('labor-cost').textContent = `NT$ ${laborCost.toFixed(2)}`;
        document.getElementById('total-batch-cost').textContent = `NT$ ${totalBatchCost.toFixed(2)}`;
        document.getElementById('avg-cost-per-product').textContent = `NT$ ${avgCostPerProduct.toFixed(2)}`;
    }

    // --- 函式：處理食譜選擇（用於創建新產品）---
    function handleRecipeSelectionForCreation(recipeId) {
        fetch(`/products/api/get_recipe_details/${recipeId}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    selectedRecipeDataForCreation = {
                        total_ingredient_cost: data.total_ingredient_cost,
                        servings_count: data.servings_count,
                        ingredient_cost_details: data.ingredient_cost_details
                    };
                    createProductModal.hide();
                    currentProductId = 'new';
                    formTitle.textContent = `新增產品 (基於: ${data.recipe_name})`;
                    renderProductForm({
                        recipe_id: recipeId,
                        product_name: `${data.recipe_name} (產品)`,
                        recipe_details: selectedRecipeDataForCreation
                    });
                    updateButtonStates();
                } else {
                    alert('獲取食譜詳情失敗: ' + data.message);
                }
            });
    }

    // --- 函式：選擇一個現有產品進行編輯 ---
    function selectProduct(productId) {
        fetch(`/products/api/products/${productId}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    currentProductId = productId;
                    selectedRecipeDataForCreation = data.recipe_details; // 儲存食譜資料以供成本計算
                    formTitle.textContent = `編輯產品: ${data.product_name}`;
                    renderProductForm(data); // 傳遞包含所有細節的 data
                    updateButtonStates();
                    document.querySelectorAll('.list-group-item.active').forEach(el => el.classList.remove('active'));
                    document.querySelector(`[data-product-id="${productId}"]`).classList.add('active');
                } else {
                    alert('獲取產品詳情失敗: ' + data.message);
                }
            });
    }
    
    // --- 函式：儲存產品（新增或更新）---
    function saveProduct() {
        const isNew = currentProductId === 'new';
        const url = isNew ? '/products/api/create_product' : `/products/api/products/${currentProductId}/update`;
        
        // 取得表單所有欄位的值
        const payload = {
            recipe_id: document.getElementById('recipe_id').value,
            product_name: document.getElementById('product_name').value,
            description: document.getElementById('description').value,
            selling_price: document.getElementById('selling_price').value,
            stock_quantity: document.getElementById('stock_quantity').value,
            batch_size: document.getElementById('batch_size').value,
            bake_power_w: document.getElementById('bake_power_w').value,
            bake_time_min: document.getElementById('bake_time_min').value,
            production_time_hr: document.getElementById('production_time_hr').value,
        };

        saveButton.disabled = true;
        saveButton.querySelector('.spinner-border').classList.remove('d-none');

        fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert(data.message);
                window.location.reload(); // 簡單起見，直接重載頁面
            } else {
                alert('儲存失敗: ' + (data.message || "請檢查欄位"));
            }
        })
        .finally(() => {
            saveButton.disabled = false;
            saveButton.querySelector('.spinner-border').classList.add('d-none');
        });
    }

    // --- 其他函式和事件監聽 (保持不變) ---
    function renderProductList(products) {
        productListDiv.innerHTML = '';
        if (products.length > 0) {
            products.forEach(product => {
                const item = document.createElement('a');
                item.href = '#';
                item.className = 'list-group-item list-group-item-action';
                item.setAttribute('data-product-id', product.id);
                item.textContent = product.name;
                item.addEventListener('click', (e) => { e.preventDefault(); selectProduct(product.id); });
                productListDiv.appendChild(item);
            });
        } else {
            productListDiv.innerHTML = '<p class="text-muted p-2 text-center">沒有找到產品。</p>';
        }
    }
    function searchProducts() { const query = productSearchBox.value.trim().toLowerCase(); const filteredProducts = allProductsInitialData.filter(p => p.name.toLowerCase().includes(query)); renderProductList(filteredProducts); }
    function renderRecipeSearchResults(recipes) { recipeSearchResultsDiv.innerHTML = ''; if (recipes.length > 0) { recipes.forEach(recipe => { const item = document.createElement('div'); item.className = 'list-group-item list-group-item-action'; item.innerHTML = `${recipe.name} <small class="text-muted">(食譜成本: NT$ ${recipe.total_ingredient_cost.toFixed(2)})</small>`; item.addEventListener('click', () => { handleRecipeSelectionForCreation(recipe.id); }); recipeSearchResultsDiv.appendChild(item); }); } else { recipeSearchResultsDiv.innerHTML = '<p class="text-muted p-2 text-center">沒有找到符合條件的食譜。</p>'; } }
    function searchRecipesInModal() { const query = recipeSearchBox.value.trim().toLowerCase(); const filteredRecipes = query === "" ? allRecipesInitialData : allRecipesInitialData.filter(r => r.name.toLowerCase().includes(query)); renderRecipeSearchResults(filteredRecipes); }
    function deleteProduct() { if (typeof currentProductId !== 'number' || !confirm('您確定要永久刪除這個產品嗎？')) return; deleteButton.disabled = true; deleteButton.querySelector('.spinner-border').classList.remove('d-none'); fetch(`/products/api/products/${currentProductId}/delete`, { method: 'POST' }).then(r => r.json()).then(d => { if (d.status === 'success') { alert(d.message); window.location.reload(); } else { alert('刪除失敗: ' + d.message); } }).finally(() => { deleteButton.disabled = false; deleteButton.querySelector('.spinner-border').classList.add('d-none'); }); }
    productSearchBox.addEventListener('input', searchProducts);
    recipeSearchBox.addEventListener('input', searchRecipesInModal);
    newButton.addEventListener('click', () => { resetToInitialState(); renderRecipeSearchResults(allRecipesInitialData); createProductModal.show(); });
    cancelButton.addEventListener('click', resetToInitialState);
    saveButton.addEventListener('click', saveProduct);
    deleteButton.addEventListener('click', deleteProduct);
    
    // --- 初始化 ---
    renderProductList(allProductsInitialData);
    resetToInitialState();
});
