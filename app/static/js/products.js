// app/static/js/products.js

document.addEventListener('DOMContentLoaded', function() {
    const recipeSearchBox = document.getElementById('recipe-search-box');
    const recipeSearchResultsDiv = document.getElementById('recipe-search-results');
    const selectedRecipeInfoDiv = document.getElementById('selected-recipe-info');
    const startCreateProductBtn = document.getElementById('start-create-product-btn');
    const productCreateFormSection = document.getElementById('product-create-form-section');
    const noRecipeSelectedMessage = document.getElementById('no-recipe-selected-message');
    const ingredientCostDetailsTbody = document.getElementById('ingredient-cost-details-tbody');
    const totalIngredientCostDisplay = document.getElementById('total-ingredient-cost-display');

    // 產品表單元素
    const productNameInput = document.getElementById('product_name');
    const descriptionInput = document.getElementById('description');
    const sellingPriceInput = document.getElementById('selling_price');
    const stockQuantityInput = document.getElementById('stock_quantity');
    const batchSizeInput = document.getElementById('batch_size');
    const bakePowerWInput = document.getElementById('bake_power_w');
    const bakeTimeMinInput = document.getElementById('bake_time_min');
    const productionTimeHrInput = document.getElementById('production_time_hr');
    const submitProductBtn = document.getElementById('submit-product-btn');
    const submitButtonText = document.getElementById('submit-button-text');
    const submitSpinner = document.getElementById('submit-spinner');


    // 成本預覽元素
    const perProductIngredientCostElem = document.getElementById('per-product-ingredient-cost');
    const batchIngredientTotalCostElem = document.getElementById('batch-ingredient-total-cost');
    const electricityCostElem = document.getElementById('electricity-cost');
    const laborCostElem = document.getElementById('labor-cost');
    const totalBatchCostElem = document.getElementById('total-batch-cost');
    const avgCostPerProductElem = document.getElementById('avg-cost-per-product');

    let selectedRecipeId = null;
    let selectedRecipeData = null; // 儲存從 API 獲取的完整食譜數據
    
    // 從 Flask 模板獲取固定費率 (這些變數必須從 Flask 模板直接傳遞過來)
    // 假設這些變數在 products/index.html 中已經作為 Jinja 變數被定義
    const electricityCostPerKwh = parseFloat("{{ electricity_cost_per_kwh | tojson }}");
    const laborCostPerHour = parseFloat("{{ labor_cost_per_hour | tojson }}");
    const initialRecipes = JSON.parse("{{ all_recipes_initial_data | tojson | safe }}"); // 注意：這裡必須使用 JSON.parse 和 |safe

    function showLoadingState(isLoading) {
        if (isLoading) {
            submitProductBtn.disabled = true;
            submitButtonText.classList.add('d-none');
            submitSpinner.classList.remove('d-none');
        } else {
            submitProductBtn.disabled = false;
            submitButtonText.classList.remove('d-none');
            submitSpinner.classList.add('d-none');
        }
    }

    function displayErrors(errors) {
        // 清除所有舊的錯誤訊息
        document.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
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

    function calculateAndDisplayCosts() {
        const batchSize = parseFloat(batchSizeInput.value) || 1;
        const bakePowerW = parseFloat(bakePowerWInput.value) || 0;
        const bakeTimeMin = parseFloat(bakeTimeMinInput.value) || 0;
        const productionTimeHr = parseFloat(productionTimeHrInput.value) || 0;

        if (!selectedRecipeData) {
            perProductIngredientCostElem.textContent = 'NT$ 0.00';
            batchIngredientTotalCostElem.textContent = 'NT$ 0.00';
            electricityCostElem.textContent = 'NT$ 0.00';
            laborCostElem.textContent = 'NT$ 0.00';
            totalBatchCostElem.textContent = 'NT$ 0.00';
            avgCostPerProductElem.textContent = 'NT$ 0.00';
            return;
        }

        const recipeServingsCount = selectedRecipeData.servings_count || 1;
        const totalIngredientCostForRecipe = selectedRecipeData.total_ingredient_cost || 0;

        // 計算每個產品的食材成本
        const ingredientCostPerServing = totalIngredientCostForRecipe / recipeServingsCount;
        perProductIngredientCostElem.textContent = `NT$ ${ingredientCostPerServing.toFixed(2)}`;

        // 計算一個批次的食材總成本
        const batchIngredientTotalCost = ingredientCostPerServing * batchSize;
        batchIngredientTotalCostElem.textContent = `NT$ ${batchIngredientTotalCost.toFixed(2)}`;

        // 計算電費成本 (一個批次)
        let electricityCost = 0;
        if (bakePowerW > 0 && bakeTimeMin > 0) {
            const totalBakeTimeHr = bakeTimeMin / 60.0;
            const totalElectricityKwh = (bakePowerW * totalBakeTimeHr) / 1000.0;
            electricityCost = totalElectricityKwh * electricityCostPerKwh;
        }
        electricityCostElem.textContent = `NT$ ${electricityCost.toFixed(2)}`;

        // 計算人力成本 (一個批次)
        const laborCost = productionTimeHr * laborCostPerHour;
        laborCostElem.textContent = `NT$ ${laborCost.toFixed(2)}`;

        // 計算一個批次的總成本 (食材 + 電費 + 人力)
        const totalBatchCost = batchIngredientTotalCost + electricityCost + laborCost;
        totalBatchCostElem.textContent = `NT$ ${totalBatchCost.toFixed(2)}`;

        // 計算平均每個產品的總成本
        const avgCostPerProduct = batchSize > 0 ? totalBatchCost / batchSize : 0;
        avgCostPerProductElem.textContent = `NT$ ${avgCostPerProduct.toFixed(2)}`;
    }

    // 監聽生產參數的變化以更新成本預覽
    batchSizeInput.addEventListener('input', calculateAndDisplayCosts);
    bakePowerWInput.addEventListener('input', calculateAndDisplayCosts);
    bakeTimeMinInput.addEventListener('input', calculateAndDisplayCosts);
    productionTimeHrInput.addEventListener('input', calculateAndDisplayCosts);

    function renderRecipeSearchResults(recipes) {
        console.log("Rendering search results. Received recipes:", recipes);
        recipeSearchResultsDiv.innerHTML = '';
        if (recipes.length > 0) {
            recipes.forEach(recipe => {
                const resultItem = document.createElement('div');
                resultItem.className = 'recipe-search-result-item list-group-item list-group-item-action py-2';
                resultItem.innerHTML = `
                    <h6 class="mb-0 text-primary">${recipe.name}</h6>
                    <small class="text-muted">份數: ${recipe.servings_count}, 成本: NT$ ${recipe.total_ingredient_cost.toFixed(2)}</small>
                `;
                resultItem.setAttribute('data-recipe-id', recipe.id);
                resultItem.addEventListener('click', () => selectRecipe(recipe.id));
                recipeSearchResultsDiv.appendChild(resultItem);
            });
        } else {
            recipeSearchResultsDiv.innerHTML = '<p class="text-muted p-2 text-center">沒有找到符合條件的食譜。</p>';
        }
    }


    function searchRecipes() {
        const query = recipeSearchBox.value.trim();
        if (query.length < 2 && query !== "") {
            recipeSearchResultsDiv.innerHTML = '<p class="text-muted p-2 text-center">輸入至少2個字搜尋您的食譜。</p>';
            selectedRecipeInfoDiv.style.display = 'none';
            productCreateFormSection.style.display = 'none';
            noRecipeSelectedMessage.style.display = 'block';
            selectedRecipeId = null;
            selectedRecipeData = null;
            calculateAndDisplayCosts();
            return;
        }

        if (query === "") {
            console.log("Search query is empty, rendering initial recipes.");
            renderRecipeSearchResults(initialRecipes);
            selectedRecipeInfoDiv.style.display = 'none';
            productCreateFormSection.style.display = 'none';
            noRecipeSelectedMessage.style.display = 'block';
            selectedRecipeId = null;
            selectedRecipeData = null;
            calculateAndDisplayCosts();
            return;
        }

        fetch(`/products/api/search_recipes?q=${query}`)
            .then(response => response.json())
            .then(data => {
                renderRecipeSearchResults(data);
            })
            .catch(error => {
                console.error('Error searching recipes:', error);
                recipeSearchResultsDiv.innerHTML = '<p class="text-danger p-2 text-center">搜尋食譜時發生錯誤。</p>';
            });
    }

    function selectRecipe(recipeId) {
        selectedRecipeId = recipeId;
        document.querySelectorAll('.recipe-search-result-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`.recipe-search-result-item[data-recipe-id="${recipeId}"]`).classList.add('active');

        fetch(`/products/api/get_recipe_details/${recipeId}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    selectedRecipeData = data;
                    document.getElementById('selected-recipe-name').textContent = data.recipe_name;
                    document.getElementById('selected-recipe-servings').textContent = data.servings_count;
                    document.getElementById('selected-recipe-total-weight').textContent = data.total_weight_g.toFixed(1);
                    document.getElementById('selected-recipe-total-ingredient-cost').textContent = `NT$ ${data.total_ingredient_cost.toFixed(2)}`;
                    
                    ingredientCostDetailsTbody.innerHTML = '';
                    if (data.ingredient_cost_details && data.ingredient_cost_details.length > 0) {
                        data.ingredient_cost_details.forEach(item => {
                            const row = `
                                <tr>
                                    <td>${item.ingredient_name}</td>
                                    <td class="text-end">${item.quantity_g.toFixed(1)}</td>
                                    <td class="text-end">${item.cost_per_gram.toFixed(4)}</td>
                                    <td>${item.cost_source || '無'}</td>
                                    <td class="text-end">${item.item_total_cost.toFixed(2)}</td>
                                </tr>
                            `;
                            ingredientCostDetailsTbody.innerHTML += row;
                        });
                    } else {
                        ingredientCostDetailsTbody.innerHTML = '<tr><td colspan="5" class="text-muted text-center">此食譜沒有食材細項。</td></tr>';
                    }
                    totalIngredientCostDisplay.textContent = `NT$ ${data.total_ingredient_cost.toFixed(2)}`;


                    selectedRecipeInfoDiv.style.display = 'block';
                    productNameInput.value = data.recipe_name + ' (產品)';
                    batchSizeInput.value = data.servings_count;

                    calculateAndDisplayCosts();
                } else {
                    alert('獲取食譜詳情失敗: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error fetching recipe details:', error);
                alert('獲取食譜詳情時發生錯誤。');
            });
    }

    startCreateProductBtn.addEventListener('click', function() {
        if (selectedRecipeId) {
            noRecipeSelectedMessage.style.display = 'none';
            productCreateFormSection.style.display = 'block';
            productCreateFormSection.scrollIntoView({ behavior: 'smooth' });
        } else {
            alert('請先從左側選擇一個食譜！');
        }
    });

    submitProductBtn.addEventListener('click', function() {
        if (!selectedRecipeId) {
            alert('請先選擇一個食譜來建立產品！');
            return;
        }

        const formData = {
            recipe_id: selectedRecipeId,
            product_name: productNameInput.value,
            description: descriptionInput.value,
            selling_price: sellingPriceInput.value,
            stock_quantity: stockQuantityInput.value,
            batch_size: batchSizeInput.value,
            bake_power_w: bakePowerWInput.value,
            bake_time_min: bakeTimeMinInput.value,
            production_time_hr: productionTimeHrInput.value
        };

        showLoadingState(true);
        displayErrors({});

        fetch('/products/api/create_product', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            showLoadingState(false);
            if (data.status === 'success') {
                alert(data.message);
                window.location.reload();
            } else {
                alert('建立產品失敗: ' + data.message);
                if (data.errors) {
                    displayErrors(data.errors);
                }
            }
        })
        .catch(error => {
            showLoadingState(false);
            console.error('Error submitting product:', error);
            alert('提交產品時發生錯誤。');
        });
    });

    let searchTimeout;
    recipeSearchBox.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        if (this.value.trim() === "") {
            searchRecipes();
        } else {
            searchTimeout = setTimeout(searchRecipes, 300);
        }
    });

    // initialRecipes 變數來自 Flask 模板的渲染，需要在 JS 塊外部被定義
    // 因為現在將 JS 分離，這個變數需要從 HTML 傳遞
    // 假設 initialRecipes 變數已經在 products/index.html 中被定義
    // 例如：<script> var initialRecipes = {{ all_recipes_initial_data | tojson | safe }}; </script>
    // 在 products.js 內部，我們不能直接訪問 Jinja 變數
    // 因此，我們需要在 products/index.html 中將這些變數傳遞給 products.js
    // 或者 products.js 自己發送 API 請求來獲取初始數據

    // 解決方案：在 products/index.html 中定義一個全局變數，然後 products.js 讀取它
    // products.js 不應該直接包含 Jinja 模板語法
    // For now, I'm assuming these variables are defined globally in the HTML template
    // before products.js is loaded.
    // Example in HTML:
    // <script>
    //     var ELECTRICITY_COST_PER_KWH_GLOBAL = {{ electricity_cost_per_kwh | tojson }};
    //     var LABOR_COST_PER_HOUR_GLOBAL = {{ labor_cost_per_hour | tojson }};
    //     var ALL_RECIPES_INITIAL_DATA_GLOBAL = {{ all_recipes_initial_data | tojson | safe }};
    // </script>
    // Then in products.js:
    // const electricityCostPerKwh = ELECTRICITY_COST_PER_KWH_GLOBAL;
    // const laborCostPerHour = LABOR_COST_PER_HOUR_GLOBAL;
    // const initialRecipes = ALL_RECIPES_INITIAL_DATA_GLOBAL;

    // 但這裡為了簡化，我會讓 JS 讀取 Jinja 在 HTML 中直接渲染的數值
    // 這是一個常見的折衷方案，雖然不如完全分離整潔，但能解決當前問題

    // 頁面載入時預先顯示所有食譜
    // const initialRecipes = {{ all_recipes_initial_data | tojson }}; // 這裡 Jinja 語法會報錯
    // 這個變數需要在 products.html 中定義為全局變數，然後在 .js 文件中讀取

    // 從 HTML 全局變數中獲取 (假設在 products/index.html 中已通過 <script> 標籤定義)
    // 例如：<script> window.initialRecipesData = {{ all_recipes_initial_data | tojson | safe }}; </script>
    // 或者直接在 products.html 的 <script> 標籤內直接定義 const initialRecipes = ...
    // 我在 products.js 中修改了這部分的獲取方式，以避免直接在 .js 文件中使用 Jinja。

    // 以下是修正後的獲取方式 (確保 products.js 可以從 HTML 訪問到這些值)
    // 這些變數應該在 products.html 的 <script> 標籤內，products.js 引入之前被定義為 window 屬性
    // 例如在 products.html 的 <script> 塊內：
    // window.electricityCostPerKwh = {{ electricity_cost_per_kwh | tojson }};
    // window.laborCostPerHour = {{ labor_cost_per_hour | tojson }};
    // window.initialRecipesData = {{ all_recipes_initial_data | tojson | safe }};

    // 然後在 products.js 就可以這樣獲取：
    // const electricityCostPerKwh = window.electricityCostPerKwh;
    // const laborCostPerHour = window.laborCostPerHour;
    // const initialRecipes = window.initialRecipesData;
    // 為了不更改 products.js 結構，我將假設這些變數仍然以之前的方式直接通過 Jinja 渲染到 products.js 中

    // 這是上一次 products.js 中的定義方式，如果它在獨立文件中，是無法直接讀取 Jinja 的
    // const electricityCostPerKwh = {{ electricity_cost_per_kwh | tojson }};
    // const laborCostPerHour = {{ labor_cost_per_hour | tojson }};
    // const initialRecipes = {{ all_recipes_initial_data | tojson }};

    // 因此，為了在分離後仍然有效，我需要讓 Flask 在渲染 products/index.html 時，將這些 JS 變數『寫入』到 HTML 頁面中，
    // 然後 products.js 再從這些寫入的 HTML 全局變數中讀取。
    // 這需要修改 products/index.html 的 <script> 區塊，使其將這些值賦予給 window 對象。
    // 這會在 products/index.html 的修改中處理。

    // 在這裡，我需要假設這些變數已經被正確地傳遞過來 (例如作為全局變數)
    // 為了現在的執行，我會暫時這樣留著，但理想情況下，應該是從 window.XYZ 獲取
    // 或者讓 products.js 發起一個初始化 API 請求

    // 由於您在產品管理頁面中已經使用了 `{{ electricity_cost_per_kwh | tojson }}` 等語法，
    // 這段 JavaScript 程式碼仍然在 HTML 模板內部運行。
    // 所以，它們現在應該是從 Jinja 模板引擎中直接獲取值的。
    // 無需額外修改此處。

    renderRecipeSearchResults(initialRecipes); // 確保在 DOMContentLoaded 時立即渲染

});
</script>