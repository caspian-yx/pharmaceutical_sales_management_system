/**
 * 仓库管理系统 - 前端交互逻辑
 * 优化点：数据缓存、动画反馈、减少DOM操作、表单验证
 */
$(document).ready(function() {
    // 缓存数据（避免重复请求）
    const cache = {
        suppliers: [],
        materials: [],
        warehouses: []
    };

    // 初始化页面
    initPage();

    // 绑定所有事件
    bindEvents();

    // -------------------------- 初始化函数 --------------------------
    function initPage() {
        // 显示加载动画
        showLoading();
        
        // 并行加载所有列表（提升首屏速度）
        Promise.all([
            loadMaterials(),
            loadSuppliers(),
            loadWarehouses(),
            loadInbounds(),
            loadOutbounds()
        ]).then(() => {
            // 初始化下拉框选项
            initSelectOptions();
            // 隐藏加载动画
            hideLoading();
        });
    }

    function initSelectOptions() {
        // 渲染供应商下拉框
        renderSupplierOptions();
        // 渲染仓库下拉框
        renderWarehouseOptions();
        // 渲染物资下拉框（用于明细）
        renderMaterialOptions();
    }

    // -------------------------- 数据加载函数 --------------------------
    // 物资列表
    function loadMaterials(params = {}) {
        return new Promise((resolve) => {
            $.getJSON("/api/materials", params, function(data) {
                cache.materials = data; // 缓存数据
                renderTable("materialTableBody", data, renderMaterialRow);
                resolve();
            });
        });
    }

    // 供应商列表
    function loadSuppliers(params = {}) {
        return new Promise((resolve) => {
            $.getJSON("/api/suppliers", params, function(data) {
                cache.suppliers = data; // 缓存数据
                renderTable("supplierTableBody", data, renderSupplierRow);
                resolve();
            });
        });
    }

    // 仓库列表
    function loadWarehouses() {
        return new Promise((resolve) => {
            $.getJSON("/api/warehouses", function(data) {
                cache.warehouses = data; // 缓存数据
                renderTable("warehouseTableBody", data, renderWarehouseRow);
                resolve();
            });
        });
    }

    // 入库单列表
    function loadInbounds(params = {}) {
        return new Promise((resolve) => {
            $.getJSON("/api/inbounds", params, function(data) {
                renderTable("inboundTableBody", data, renderInboundRow);
                resolve();
            });
        });
    }

    // 出库单列表
    function loadOutbounds(params = {}) {
        return new Promise((resolve) => {
            $.getJSON("/api/outbounds", params, function(data) {
                renderTable("outboundTableBody", data, renderOutboundRow);
                resolve();
            });
        });
    }

    // -------------------------- 渲染函数（带动画） --------------------------
    // 通用表格渲染（减少DOM操作，添加淡入动画）
    function renderTable(tableId, data, rowRender) {
        const $table = $(`#${tableId}`);
        const htmlArr = [];

        if (data.length === 0) {
            htmlArr.push('<tr><td colspan="10" class="text-center text-muted py-3">暂无数据</td></tr>');
        } else {
            data.forEach(item => htmlArr.push(rowRender(item)));
        }

        // 淡入动画
        $table.fadeOut(100, () => {
            $table.html(htmlArr.join('')).fadeIn(200);
        });
    }

    // 物资行渲染
    function renderMaterialRow(mat) {
        return `
            <tr>
                <td>${mat.material_id}</td>
                <td>${mat.name}</td>
                <td>${mat.category || '-'}</td>
                <td>${mat.unit}</td>
                <td class="text-primary fw-bold">${mat.stock}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary hover-lift" onclick="editMaterial(${mat.material_id})">编辑</button>
                    <button class="btn btn-sm btn-outline-danger hover-lift ms-1" onclick="deleteMaterial(${mat.material_id})">删除</button>
                </td>
            </tr>
        `;
    }

    // 供应商行渲染
    function renderSupplierRow(sup) {
        const statusClass = sup.is_valid === "有效" ? "text-success" : "text-secondary";
        return `
            <tr>
                <td>${sup.supplier_id}</td>
                <td>${sup.supplier_name}</td>
                <td>${sup.contact_person || '-'}</td>
                <td>${sup.phone || '-'}</td>
                <td class="${statusClass} fw-medium">${sup.is_valid}</td>
                <td>
                    <button class="btn btn-sm btn-outline-success hover-lift" onclick="editSupplier(${sup.supplier_id})">编辑</button>
                    <button class="btn btn-sm btn-outline-danger hover-lift ms-1" onclick="deleteSupplier(${sup.supplier_id})">删除</button>
                </td>
            </tr>
        `;
    }

    // 仓库行渲染
    function renderWarehouseRow(wh) {
        return `
            <tr>
                <td>${wh.warehouse_id}</td>
                <td>${wh.name}</td>
                <td>${wh.location || '-'}</td>
                <td>
                    <button class="btn btn-sm btn-outline-dark hover-lift" onclick="editWarehouse(${wh.warehouse_id})">编辑</button>
                    <button class="btn btn-sm btn-outline-danger hover-lift ms-1" onclick="deleteWarehouse(${wh.warehouse_id})">删除</button>
                </td>
            </tr>
        `;
    }

    // 入库单行渲染
    function renderInboundRow(inb) {
        let statusClass = "";
        if (inb.audit_status === "已通过") statusClass = "text-success";
        else if (inb.audit_status === "已驳回") statusClass = "text-danger";
        else statusClass = "text-warning";
        
        return `
            <tr>
                <td>${inb.inbound_id}</td>
                <td>${inb.supplier_name}</td>
                <td>${inb.name}</td>
                <td>${inb.inbound_date}</td>
                <td class="${statusClass} fw-medium">${inb.audit_status}</td>
                <td>${inb.remark || '-'}</td>
                <td>
                    <button class="btn btn-sm btn-outline-info hover-lift" onclick="editInbound('${inb.inbound_id}')">编辑</button>
                    <button class="btn btn-sm btn-outline-danger hover-lift ms-1" onclick="deleteInbound('${inb.inbound_id}')">删除</button>
                </td>
            </tr>
        `;
    }

    // 出库单行渲染
    function renderOutboundRow(outb) {
        let statusClass = "";
        if (outb.audit_status === "已通过") statusClass = "text-success";
        else if (outb.audit_status === "已驳回") statusClass = "text-danger";
        else statusClass = "text-warning";
        
        return `
            <tr>
                <td>${outb.outbound_id}</td>
                <td>${outb.dept_name}</td>
                <td>${outb.name}</td>
                <td>${outb.outbound_date}</td>
                <td class="${statusClass} fw-medium">${outb.audit_status}</td>
                <td>${outb.remark || '-'}</td>
                <td>
                    <button class="btn btn-sm btn-outline-warning hover-lift" onclick="editOutbound('${outb.outbound_id}')">编辑</button>
                    <button class="btn btn-sm btn-outline-danger hover-lift ms-1" onclick="deleteOutbound('${outb.outbound_id}')">删除</button>
                </td>
            </tr>
        `;
    }

    // 渲染下拉框选项
    function renderSupplierOptions() {
        let options = '<option value="">所有供应商</option>';
        cache.suppliers.forEach(s => {
            options += `<option value="${s.supplier_id}">${s.supplier_name}</option>`;
        });
        $("#inboundSupplierSelect").html(options);
        $("#inboundSupplierId").html(options.replace('<option value="">所有供应商</option>', '<option value="">请选择供应商</option>'));
    }

    function renderWarehouseOptions() {
        let options = '<option value="">请选择仓库</option>';
        cache.warehouses.forEach(w => {
            options += `<option value="${w.warehouse_id}">${w.name}</option>`;
        });
        $("#inboundWarehouseId").html(options);
        $("#outboundWarehouseId").html(options);
    }

    function renderMaterialOptions() {
        // 入库明细物资选项
        let inOptions = '<option value="">请选择物资</option>';
        // 出库明细物资选项（带库存）
        let outOptions = '<option value="">请选择物资</option>';
        
        cache.materials.forEach(m => {
            inOptions += `<option value="${m.material_id}">${m.name}（${m.unit}）</option>`;
            outOptions += `<option value="${m.material_id}">${m.name}（库存：${m.stock} ${m.unit}）</option>`;
        });
        
        $(".inbound-material").html(inOptions);
        $(".outbound-material").html(outOptions);
    }

    // -------------------------- 事件绑定 --------------------------
    function bindEvents() {
        // 物资表单提交
        $("#materialForm").submit(function(e) {
            e.preventDefault();
            submitForm({
                formId: "materialForm",
                modalId: "materialModal",
                url: () => $("#materialId").val() ? `/api/materials/${$("#materialId").val()}` : "/api/materials",
                method: () => $("#materialId").val() ? "PUT" : "POST",
                data: () => ({
                    name: $("#materialName").val(),
                    category: $("#materialCategory").val(),
                    unit: $("#materialUnit").val(),
                    stock: $("#materialStock").val()
                }),
                success: () => loadMaterials()
            });
        });

        // 供应商表单提交
        $("#supplierForm").submit(function(e) {
            e.preventDefault();
            submitForm({
                formId: "supplierForm",
                modalId: "supplierModal",
                url: () => $("#supplierId").val() ? `/api/suppliers/${$("#supplierId").val()}` : "/api/suppliers",
                method: () => $("#supplierId").val() ? "PUT" : "POST",
                data: () => ({
                    name: $("#supplierName").val(),
                    contact: $("#supplierContact").val(),
                    phone: $("#supplierPhone").val(),
                    is_valid: $("#supplierIsValid").is(":checked")
                }),
                success: () => {
                    loadSuppliers();
                    renderSupplierOptions(); // 刷新下拉框
                }
            });
        });

        // 仓库表单提交
        $("#warehouseForm").submit(function(e) {
            e.preventDefault();
            submitForm({
                formId: "warehouseForm",
                modalId: "warehouseModal",
                url: () => $("#warehouseId").val() ? `/api/warehouses/${$("#warehouseId").val()}` : "/api/warehouses",
                method: () => $("#warehouseId").val() ? "PUT" : "POST",
                data: () => ({
                    name: $("#warehouseName").val(),
                    location: $("#warehouseLocation").val()
                }),
                success: () => {
                    loadWarehouses();
                    renderWarehouseOptions(); // 刷新下拉框
                }
            });
        });

        // 入库单表单提交
        $("#inboundForm").submit(function(e) {
            e.preventDefault();
            const details = collectInboundDetails();
            if (!details) return;

            submitForm({
                formId: "inboundForm",
                modalId: "inboundModal",
                url: () => $("#inboundId").val() ? `/api/inbounds/${$("#inboundId").val()}` : "/api/inbounds",
                method: () => $("#inboundId").val() ? "PUT" : "POST",
                data: () => ({
                    supplier_id: $("#inboundSupplierId").val(),
                    warehouse_id: $("#inboundWarehouseId").val(),
                    date: $("#inboundDate").val(),
                    audit_status: $("#inboundAuditStatus").val(),
                    remark: $("#inboundRemark").val(),
                    details: details
                }),
                success: () => {
                    loadInbounds();
                    loadMaterials(); // 刷新库存
                }
            });
        });

        // 出库单表单提交
        $("#outboundForm").submit(function(e) {
            e.preventDefault();
            const details = collectOutboundDetails();
            if (!details) return;

            submitForm({
                formId: "outboundForm",
                modalId: "outboundModal",
                url: () => $("#outboundId").val() ? `/api/outbounds/${$("#outboundId").val()}` : "/api/outbounds",
                method: () => $("#outboundId").val() ? "PUT" : "POST",
                data: () => ({
                    dept_name: $("#outboundDeptName").val(),
                    warehouse_id: $("#outboundWarehouseId").val(),
                    date: $("#outboundDate").val(),
                    audit_status: $("#outboundAuditStatus").val(),
                    remark: $("#outboundRemark").val(),
                    details: details
                }),
                success: () => {
                    loadOutbounds();
                    loadMaterials(); // 刷新库存
                }
            });
        });

        // 查询表单提交
        $("#materialSearchForm").submit(function(e) {
            e.preventDefault();
            const params = getFormParams("materialSearchForm");
            loadMaterials(params);
        });

        $("#supplierSearchForm").submit(function(e) {
            e.preventDefault();
            const params = getFormParams("supplierSearchForm");
            loadSuppliers(params);
        });

        $("#inboundSearchForm").submit(function(e) {
            e.preventDefault();
            const params = getFormParams("inboundSearchForm");
            loadInbounds(params);
        });

        $("#outboundSearchForm").submit(function(e) {
            e.preventDefault();
            const params = getFormParams("outboundSearchForm");
            loadOutbounds(params);
        });
    }

    // -------------------------- 工具函数 --------------------------
    // 显示加载动画
    function showLoading() {
        $("body").append(`
            <div id="loading" style="position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(255,255,255,0.8); z-index:9999; display:flex; align-items:center; justify-content:center;">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
            </div>
        `);
    }

    // 隐藏加载动画
    function hideLoading() {
        $("#loading").fadeOut(300, () => $("#loading").remove());
    }

    // 收集表单参数
    function getFormParams(formId) {
        return $(`#${formId}`).serializeArray().reduce((obj, item) => {
            if (item.value) obj[item.name] = item.value;
            return obj;
        }, {});
    }

    // 通用表单提交（带加载状态和成功提示）
    function submitForm({ formId, modalId, url, method, data, success }) {
        const $form = $(`#${formId}`);
        const $submitBtn = $form.find('button[type="submit"]');
        
        // 禁用提交按钮，防止重复提交
        $submitBtn.prop("disabled", true).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 提交中...');

        $.ajax({
            url: url(),
            type: method(),
            contentType: "application/json",
            data: JSON.stringify(data()),
            success: function() {
                $(`#${modalId}`).modal("hide");
                success(); // 刷新列表
                showToast("操作成功！", "success"); // 成功提示
            },
            error: function() {
                showToast("操作失败，请重试", "danger"); // 失败提示
            },
            complete: function() {
                // 恢复按钮状态
                $submitBtn.prop("disabled", false).text("保存");
            }
        });
    }

    // 显示提示框（带动画）
    function showToast(message, type = "info") {
        const toastId = `toast-${Date.now()}`;
        $("body").append(`
            <div id="${toastId}" class="toast position-fixed bottom-3 end-3 bg-${type} text-white" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-body d-flex align-items-center">
                    <span>${message}</span>
                    <button type="button" class="btn-close btn-close-white ms-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `);
        const toast = new bootstrap.Toast($(`#${toastId}`)[0]);
        toast.show();
        // 3秒后自动移除
        setTimeout(() => $(`#${toastId}`).remove(), 3000);
    }

    // 收集入库明细
    function collectInboundDetails() {
        const details = [];
        let isValid = true;
        
        $("#inboundDetailsTable tr").each(function() {
            const materialId = $(this).find(".inbound-material").val();
            const quantity = $(this).find(".inbound-quantity").val();
            const price = $(this).find(".inbound-price").val();
            
            // 验证
            if (!materialId) {
                highlightInvalid($(this).find(".inbound-material"), "请选择物资");
                isValid = false;
            }
            if (!quantity || quantity < 1) {
                highlightInvalid($(this).find(".inbound-quantity"), "数量至少为1");
                isValid = false;
            }
            if (!price || price < 0.01) {
                highlightInvalid($(this).find(".inbound-price"), "单价至少为0.01");
                isValid = false;
            }
            
            if (isValid) {
                details.push({
                    material_id: materialId,
                    quantity: quantity,
                    unit_price: price
                });
            }
        });
        
        return isValid ? details : null;
    }

    // 收集出库明细
    function collectOutboundDetails() {
        const details = [];
        let isValid = true;
        
        $("#outboundDetailsTable tr").each(function() {
            const materialId = $(this).find(".outbound-material").val();
            const quantity = $(this).find(".outbound-quantity").val();
            
            // 验证
            if (!materialId) {
                highlightInvalid($(this).find(".outbound-material"), "请选择物资");
                isValid = false;
            }
            if (!quantity || quantity < 1) {
                highlightInvalid($(this).find(".outbound-quantity"), "数量至少为1");
                isValid = false;
            }
            
            if (isValid) {
                details.push({
                    material_id: materialId,
                    quantity: quantity
                });
            }
        });
        
        return isValid ? details : null;
    }

    // 高亮无效字段（带抖动动画）
    function highlightInvalid($el, message) {
        $el.addClass("border-danger is-invalid");
        // 添加抖动动画
        $el.css("animation", "shake 0.5s");
        setTimeout(() => $el.css("animation", ""), 500);
        // 移除高亮（输入时）
        $el.on("input change", function() {
            $el.removeClass("border-danger is-invalid");
        });
        showToast(message, "danger");
    }

    // -------------------------- 全局函数（供HTML调用） --------------------------
    // 物资相关
    window.resetMaterialForm = function() {
        $("#materialId").val("");
        $("#materialName").val("");
        $("#materialCategory").val("");
        $("#materialUnit").val("");
        $("#materialStock").val(0);
        $("#materialModalTitle").text("添加物资");
    };

    window.editMaterial = function(id) {
        const mat = cache.materials.find(m => m.material_id === id);
        if (mat) {
            $("#materialId").val(mat.material_id);
            $("#materialName").val(mat.name);
            $("#materialCategory").val(mat.category);
            $("#materialUnit").val(mat.unit);
            $("#materialStock").val(mat.stock);
            $("#materialModalTitle").text("编辑物资");
            $("#materialModal").modal("show");
        }
    };

    window.deleteMaterial = function(id) {
        if (confirm("确认删除该物资？")) {
            $.ajax({
                url: `/api/materials/${id}`,
                type: "DELETE",
                success: function() {
                    loadMaterials();
                    showToast("删除成功", "success");
                }
            });
        }
    };

    // 供应商相关
    window.resetSupplierForm = function() {
        $("#supplierId").val("");
        $("#supplierName").val("");
        $("#supplierContact").val("");
        $("#supplierPhone").val("");
        $("#supplierIsValid").prop("checked", true);
        $("#supplierModalTitle").text("添加供应商");
    };

    window.editSupplier = function(id) {
        const sup = cache.suppliers.find(s => s.supplier_id === id);
        if (sup) {
            $("#supplierId").val(sup.supplier_id);
            $("#supplierName").val(sup.supplier_name);
            $("#supplierContact").val(sup.contact_person);
            $("#supplierPhone").val(sup.phone);
            $("#supplierIsValid").prop("checked", sup.is_valid === "有效");
            $("#supplierModalTitle").text("编辑供应商");
            $("#supplierModal").modal("show");
        }
    };

    window.deleteSupplier = function(id) {
        if (confirm("确认删除该供应商？")) {
            $.ajax({
                url: `/api/suppliers/${id}`,
                type: "DELETE",
                success: function() {
                    loadSuppliers();
                    renderSupplierOptions();
                    showToast("删除成功", "success");
                }
            });
        }
    };

    // 仓库相关
    window.resetWarehouseForm = function() {
        $("#warehouseId").val("");
        $("#warehouseName").val("");
        $("#warehouseLocation").val("");
        $("#warehouseModalTitle").text("添加仓库");
    };

    window.editWarehouse = function(id) {
        const wh = cache.warehouses.find(w => w.warehouse_id === id);
        if (wh) {
            $("#warehouseId").val(wh.warehouse_id);
            $("#warehouseName").val(wh.name);
            $("#warehouseLocation").val(wh.location);
            $("#warehouseModalTitle").text("编辑仓库");
            $("#warehouseModal").modal("show");
        }
    };

    window.deleteWarehouse = function(id) {
        if (confirm("确认删除该仓库？")) {
            $.ajax({
                url: `/api/warehouses/${id}`,
                type: "DELETE",
                success: function() {
                    loadWarehouses();
                    renderWarehouseOptions();
                    showToast("删除成功", "success");
                }
            });
        }
    };

    // 入库单相关
    window.resetInboundForm = function() {
        $("#inboundId").val("");
        $("#inboundSupplierId").val("");
        $("#inboundWarehouseId").val("");
        $("#inboundDate").val(new Date().toISOString().split('T')[0]);
        $("#inboundAuditStatus").val(0);
        $("#inboundRemark").val("");
        $("#inboundDetailsTable").html(`
            <tr>
                <td><select class="form-select form-select-sm inbound-material"></select></td>
                <td><input type="number" class="form-control form-control-sm inbound-quantity" min="1" value="1"></td>
                <td><input type="number" class="form-control form-control-sm inbound-price" min="0.01" step="0.01" value="0.01"></td>
                <td><button type="button" class="btn btn-danger btn-sm" onclick="removeInboundDetail(this)">-</button></td>
            </tr>
        `);
        renderMaterialOptions(); // 刷新物资选项
        $("#inboundModalTitle").text("添加入库单");
    };

    window.addInboundDetail = function() {
        $("#inboundDetailsTable").append(`
            <tr>
                <td><select class="form-select form-select-sm inbound-material"></select></td>
                <td><input type="number" class="form-control form-control-sm inbound-quantity" min="1" value="1"></td>
                <td><input type="number" class="form-control form-control-sm inbound-price" min="0.01" step="0.01" value="0.01"></td>
                <td><button type="button" class="btn btn-danger btn-sm" onclick="removeInboundDetail(this)">-</button></td>
            </tr>
        `);
        renderMaterialOptions(); // 刷新物资选项
    };

    window.removeInboundDetail = function(btn) {
        if ($("#inboundDetailsTable tr").length > 1) {
            $(btn).closest("tr").remove();
        } else {
            showToast("至少保留一条明细", "warning");
        }
    };

    window.editInbound = function(id) {
        resetInboundForm();
        $("#inboundId").val(id);
        $("#inboundModalTitle").text("编辑入库单");
        $("#inboundModal").modal("show");
    };

    window.deleteInbound = function(id) {
        if (confirm("确认删除该入库单？将同步减少库存")) {
            $.ajax({
                url: `/api/inbounds/${id}`,
                type: "DELETE",
                success: function() {
                    loadInbounds();
                    loadMaterials();
                    showToast("删除成功", "success");
                }
            });
        }
    };

    // 出库单相关
    window.resetOutboundForm = function() {
        $("#outboundId").val("");
        $("#outboundDeptName").val("");
        $("#outboundWarehouseId").val("");
        $("#outboundDate").val(new Date().toISOString().split('T')[0]);
        $("#outboundAuditStatus").val(0);
        $("#outboundRemark").val("");
        $("#outboundDetailsTable").html(`
            <tr>
                <td><select class="form-select form-select-sm outbound-material"></select></td>
                <td><input type="number" class="form-control form-control-sm outbound-quantity" min="1" value="1"></td>
                <td><button type="button" class="btn btn-danger btn-sm" onclick="removeOutboundDetail(this)">-</button></td>
            </tr>
        `);
        renderMaterialOptions(); // 刷新物资选项
        $("#outboundModalTitle").text("添加出库单");
    };

    window.addOutboundDetail = function() {
        $("#outboundDetailsTable").append(`
            <tr>
                <td><select class="form-select form-select-sm outbound-material"></select></td>
                <td><input type="number" class="form-control form-control-sm outbound-quantity" min="1" value="1"></td>
                <td><button type="button" class="btn btn-danger btn-sm" onclick="removeOutboundDetail(this)">-</button></td>
            </tr>
        `);
        renderMaterialOptions(); // 刷新物资选项
    };

    window.removeOutboundDetail = function(btn) {
        if ($("#outboundDetailsTable tr").length > 1) {
            $(btn).closest("tr").remove();
        } else {
            showToast("至少保留一条明细", "warning");
        }
    };

    window.editOutbound = function(id) {
        resetOutboundForm();
        $("#outboundId").val(id);
        $("#outboundModalTitle").text("编辑出库单");
        $("#outboundModal").modal("show");
    };

    window.deleteOutbound = function(id) {
        if (confirm("确认删除该出库单？将同步增加库存")) {
            $.ajax({
                url: `/api/outbounds/${id}`,
                type: "DELETE",
                success: function() {
                    loadOutbounds();
                    loadMaterials();
                    showToast("删除成功", "success");
                }
            });
        }
    };

    // 重置查询
    window.resetMaterialSearch = function() {
        $("#materialSearchForm")[0].reset();
        loadMaterials();
    };

    window.resetSupplierSearch = function() {
        $("#supplierSearchForm")[0].reset();
        loadSuppliers();
    };

    window.resetInboundSearch = function() {
        $("#inboundSearchForm")[0].reset();
        loadInbounds();
    };

    window.resetOutboundSearch = function() {
        $("#outboundSearchForm")[0].reset();
        loadOutbounds();
    };

    // 添加全局样式（动画效果）
    const style = document.createElement('style');
    style.textContent = `
        /* 按钮悬停提升效果 */
        .hover-lift {
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .hover-lift:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        /* 抖动动画（用于表单验证） */
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
            20%, 40%, 60%, 80% { transform: translateX(5px); }
        }
        /* 表格行悬停效果 */
        table tbody tr {
            transition: background-color 0.2s;
        }
    `;
    document.head.appendChild(style);
});