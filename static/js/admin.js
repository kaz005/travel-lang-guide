// 画像入力フィールドを追加する関数
function addImageInput(mode) {
    const container = document.getElementById(mode === 'create' ? 'createImageInputs' : 'editImageInputs');
    const imageInput = document.createElement('div');
    imageInput.className = 'image-input mb-3';
    imageInput.innerHTML = `
        <div class="input-group mb-2">
            <input type="text" class="form-control" name="image_urls[]" placeholder="画像URL">
            <button type="button" class="btn btn-outline-danger" onclick="removeImageInput(this)">
                <i class="fas fa-trash"></i>
            </button>
        </div>
        <div class="mb-2">
            <label class="form-label">キャプション</label>
            <div class="input-group mb-2">
                <span class="input-group-text">🇯🇵</span>
                <input type="text" class="form-control" name="image_captions_ja[]" placeholder="キャプション（日本語）">
            </div>
            <div class="input-group mb-2">
                <span class="input-group-text">🇺🇸</span>
                <input type="text" class="form-control" name="image_captions_en[]" placeholder="Caption (English)">
            </div>
            <div class="input-group">
                <span class="input-group-text">🇨🇳</span>
                <input type="text" class="form-control" name="image_captions_zh[]" placeholder="标题（中文）">
            </div>
        </div>
        <div>
            <label class="form-label">説明文</label>
            <div class="mb-2">
                <span>🇯🇵</span>
                <textarea class="form-control" name="image_descriptions_ja[]" rows="3" placeholder="写真の説明（日本語）"></textarea>
            </div>
            <div class="mb-2">
                <span>🇺🇸</span>
                <textarea class="form-control" name="image_descriptions_en[]" rows="3" placeholder="Photo description (English)"></textarea>
            </div>
            <div>
                <span>🇨🇳</span>
                <textarea class="form-control" name="image_descriptions_zh[]" rows="3" placeholder="照片描述（中文）"></textarea>
            </div>
        </div>
    `;
    container.appendChild(imageInput);
}

// 画像入力フィールドを削除する関数
function removeImageInput(button) {
    button.closest('.image-input').remove();
}

// 編集モーダルを設定する関数
function setupEditModal(spotData) {
    const form = document.getElementById('editForm');
    form.action = `/admin/spots/${spotData.id}/update`;

    // 基本情報を設定
    form.querySelector('[name="name_ja"]').value = spotData.name.ja;
    form.querySelector('[name="name_en"]').value = spotData.name.en;
    form.querySelector('[name="name_zh"]').value = spotData.name.zh;
    form.querySelector('[name="desc_ja"]').value = spotData.description.ja;
    form.querySelector('[name="desc_en"]').value = spotData.description.en;
    form.querySelector('[name="desc_zh"]').value = spotData.description.zh;
    form.querySelector('[name="lat"]').value = spotData.coordinates.lat;
    form.querySelector('[name="lng"]').value = spotData.coordinates.lng;

    // 画像入力フィールドをクリア
    const imageInputs = document.getElementById('editImageInputs');
    imageInputs.innerHTML = '';

    // 既存の画像情報を設定
    if (spotData.images && spotData.images.length > 0) {
        spotData.images.forEach(image => {
            const imageInput = document.createElement('div');
            imageInput.className = 'image-input mb-3';
            imageInput.innerHTML = `
                <div class="input-group mb-2">
                    <input type="text" class="form-control" name="image_urls[]" value="${image.url}" placeholder="画像URL">
                    <button type="button" class="btn btn-outline-danger" onclick="removeImageInput(this)">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
                <div class="mb-2">
                    <label class="form-label">キャプション</label>
                    <div class="input-group mb-2">
                        <span class="input-group-text">🇯🇵</span>
                        <input type="text" class="form-control" name="image_captions_ja[]" value="${image.caption.ja}" placeholder="キャプション（日本語）">
                    </div>
                    <div class="input-group mb-2">
                        <span class="input-group-text">🇺🇸</span>
                        <input type="text" class="form-control" name="image_captions_en[]" value="${image.caption.en}" placeholder="Caption (English)">
                    </div>
                    <div class="input-group">
                        <span class="input-group-text">🇨🇳</span>
                        <input type="text" class="form-control" name="image_captions_zh[]" value="${image.caption.zh}" placeholder="标题（中文）">
                    </div>
                </div>
                <div>
                    <label class="form-label">説明文</label>
                    <div class="mb-2">
                        <span>🇯🇵</span>
                        <textarea class="form-control" name="image_descriptions_ja[]" rows="3" placeholder="写真の説明（日本語）">${image.description.ja}</textarea>
                    </div>
                    <div class="mb-2">
                        <span>🇺🇸</span>
                        <textarea class="form-control" name="image_descriptions_en[]" rows="3" placeholder="Photo description (English)">${image.description.en}</textarea>
                    </div>
                    <div>
                        <span>🇨🇳</span>
                        <textarea class="form-control" name="image_descriptions_zh[]" rows="3" placeholder="照片描述（中文）">${image.description.zh}</textarea>
                    </div>
                </div>
            `;
            imageInputs.appendChild(imageInput);
        });
    }
}

// 編集ボタンのイベントリスナーを設定
document.addEventListener('DOMContentLoaded', function() {
    const editButtons = document.querySelectorAll('.edit-button');
    editButtons.forEach(button => {
        button.addEventListener('click', function() {
            const spotData = JSON.parse(this.dataset.spot);
            setupEditModal(spotData);
            const editModal = new bootstrap.Modal(document.getElementById('editSpotModal'));
            editModal.show();
        });
    });
}); 