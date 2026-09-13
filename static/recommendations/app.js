const form = document.querySelector("#recommendation-form");
const errorBox = document.querySelector("#form-error");
const resultList = document.querySelector("#result-list");
const resultCount = document.querySelector("#result-count");
const submitButton = document.querySelector("#submit-button");
const resultsPanel = document.querySelector(".results-card");
const exactBudget = document.querySelector("#exact-budget");
const budgetRange = document.querySelector("#budget-range");
const rangeInputs = [...budgetRange.querySelectorAll("input")];

const labels = {
    "office desk": "میز اداری", "office chair": "صندلی اداری", "file cabinet": "فایلینگ", bookshelf: "کتابخانه", "reception counter": "کانتر پذیرش", "waiting area sofa": "مبل انتظار",
    modern: "مدرن", classic: "کلاسیک", minimal: "مینیمال", industrial: "صنعتی", black: "مشکی", white: "سفید", gray: "خاکستری", brown: "قهوه‌ای", cream: "کرم",
};
const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[character]));

function payloadFromForm() {
    const raw = Object.fromEntries(new FormData(form).entries());
    const payload = { person: raw.person, productType: raw.productType, number_of_person: Number(raw.number_of_person) };
    for (const field of ["budget", "budget_min", "budget_max"]) if (raw[field] !== "") payload[field] = Number(raw[field]);
    for (const field of ["style", "color", "fabric_material", "body_material"]) if (raw[field] !== "") payload[field] = raw[field];
    return payload;
}

function setBudgetMode() {
    const usingRange = budgetRange.open;
    exactBudget.disabled = usingRange;
    if (usingRange) exactBudget.value = "";
    if (!usingRange) rangeInputs.forEach((input) => { input.value = ""; });
}

function formatLabel(value) { return labels[value] || value || "نامشخص"; }
function formatPrice(value) { return `${Number(value).toLocaleString("fa-IR")} تومان`; }

function renderProducts(items) {
    resultCount.textContent = `${items.length} گزینه`;
    if (!items.length) {
        resultList.innerHTML = '<div class="empty-state"><span aria-hidden="true" class="empty-mark">!</span><h3>گزینه‌ای پیدا نشد</h3><p>نوع محصول یا ترجیحاتتان را تغییر دهید و دوباره امتحان کنید.</p></div>';
        return;
    }
    resultList.innerHTML = items.map(({ rank, score, product }) => `
        <article class="product"><div class="product-title"><h3>${escapeHtml(formatLabel(product.productType))} شماره ${escapeHtml(product.id)}</h3><span class="rank">رتبهٔ ${escapeHtml(rank)}</span></div>
        <span class="match-score">امتیاز تطابق: ${escapeHtml(score)}</span><div class="meta"><span>${escapeHtml(formatPrice(product.budget))}</span><span>ظرفیت ${escapeHtml(product.number_of_person)} نفر</span><span>${escapeHtml(formatLabel(product.style))}</span><span>${escapeHtml(formatLabel(product.color))}</span></div></article>`).join("");
}

function setEmptyResult(title, message, isLoading = false) {
    resultCount.textContent = isLoading ? "در حال بررسی" : "";
    resultList.innerHTML = `<div class="empty-state ${isLoading ? "loading-state" : ""}"><span aria-hidden="true" class="empty-mark">${isLoading ? "…" : "!"}</span><h3>${title}</h3><p>${message}</p></div>`;
}

function readableError(data) {
    if (typeof data === "string") return data;
    if (data?.detail) return data.detail;
    const messages = Object.values(data || {}).flatMap((value) => Array.isArray(value) ? value : [value]).filter(Boolean);
    return messages.join(" ") || "دریافت پیشنهادها با خطا مواجه شد.";
}

function budgetRangeError() {
    const [minimum, maximum] = rangeInputs.map((input) => input.value);
    if ((minimum && !maximum) || (!minimum && maximum)) return "برای بودجهٔ بازه‌ای، حداقل و حداکثر را هر دو وارد کنید.";
    if (minimum && maximum && Number(minimum) > Number(maximum)) return "حداقل بودجه نمی‌تواند بیشتر از حداکثر بودجه باشد.";
    return null;
}

budgetRange.addEventListener("toggle", setBudgetMode);
exactBudget.addEventListener("input", () => {
    if (exactBudget.value) {
        budgetRange.open = false;
        rangeInputs.forEach((input) => { input.value = ""; });
    }
});

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorBox.hidden = true;
    if (!form.checkValidity()) { form.reportValidity(); return; }
    const rangeError = budgetRangeError();
    if (rangeError) {
        errorBox.textContent = rangeError;
        errorBox.hidden = false;
        return;
    }

    submitButton.disabled = true;
    resultsPanel.setAttribute("aria-busy", "true");
    setEmptyResult("در حال بررسی گزینه‌ها", "چند لحظه صبر کنید؛ انتخاب‌های مناسب در حال مرتب‌سازی هستند.", true);
    try {
        const response = await fetch("/api/v1/recommendations/", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payloadFromForm()) });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            const error = new Error(readableError(data));
            error.isValidationError = response.status >= 400 && response.status < 500;
            throw error;
        }
        renderProducts(data.recommendations || []);
        if (window.matchMedia("(max-width: 850px)").matches) resultsPanel.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (error) {
        errorBox.textContent = error.message || "دریافت پیشنهادها با خطا مواجه شد.";
        errorBox.hidden = false;
        if (!error.isValidationError) setEmptyResult("دوباره تلاش کنید", "ارتباط با سرویس پیشنهاددهی برقرار نشد.");
    } finally {
        submitButton.disabled = false;
        resultsPanel.setAttribute("aria-busy", "false");
    }
});
