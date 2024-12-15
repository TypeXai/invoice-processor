document.addEventListener("DOMContentLoaded", () => {
  // API Configuration
  const API_URL =
    window.location.hostname === "localhost"
      ? "http://localhost:5000"
      : "https://gemini-invoice-processor.onrender.com"; // Updated Render URL

  const uploadForm = document.getElementById("uploadForm");
  const invoiceFile = document.getElementById("invoiceFile");
  const loadingOverlay = document.getElementById("loadingOverlay");
  const resultDiv = document.getElementById("result");

  uploadForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    if (!invoiceFile.files[0]) {
      alert("Please select a file");
      return;
    }

    const file = invoiceFile.files[0];

    // Validate file type and size
    if (!file.type.match("image.*")) {
      alert("Please upload an image file");
      return;
    }

    if (file.size > 6 * 1024 * 1024) {
      alert("File size should be less than 6MB");
      return;
    }

    try {
      loadingOverlay.style.display = "flex";

      // Track upload start
      window.firebaseService.trackInteraction("upload_start", {
        fileSize: file.size,
        fileType: file.type,
      });

      // Upload to Firebase Storage
      const downloadURL = await window.firebaseService.uploadInvoice(file);

      // Create form data for processing
      const formData = new FormData();
      formData.append("file", file);
      formData.append("firebase_url", downloadURL);

      // Process with backend
      const response = await fetch(`${API_URL}/upload`, {
        method: "POST",
        body: formData,
        headers: {
          Accept: "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.status === "success") {
        // Log successful processing
        window.firebaseService.logProcessing(true, data.processing_time);

        // Display results
        displayResults(data.invoice_data);
      } else {
        throw new Error(data.error || "Processing failed");
      }
    } catch (error) {
      console.error("Error:", error);

      // Log error
      window.firebaseService.logProcessing(false, 0, error.message);

      alert(`Error processing invoice: ${error.message}`);
      resultDiv.style.display = "none";
    } finally {
      loadingOverlay.style.display = "none";
    }
  });

  function displayResults(invoiceData) {
    resultDiv.innerHTML = `
      <h3>Processing Results</h3>
      <div class="table-responsive">
        <table class="table table-bordered">
          <thead>
            <tr>
              <th>Item Code</th>
              <th>Description</th>
              <th>Quantity</th>
              <th>Price</th>
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            ${invoiceData.line_items
              .map(
                (item) => `
              <tr>
                <td>${item.item_code}</td>
                <td>${item.description}</td>
                <td>${item.quantity}</td>
                <td>${formatCurrency(item.price)}</td>
                <td>${formatCurrency(item.total)}</td>
              </tr>
            `
              )
              .join("")}
          </tbody>
          <tfoot>
            <tr>
              <td colspan="4" class="text-end"><strong>Subtotal:</strong></td>
              <td>${formatCurrency(invoiceData.totals.subtotal)}</td>
            </tr>
            <tr>
              <td colspan="4" class="text-end"><strong>Tax:</strong></td>
              <td>${formatCurrency(invoiceData.totals.tax)}</td>
            </tr>
            <tr>
              <td colspan="4" class="text-end"><strong>Total:</strong></td>
              <td>${formatCurrency(invoiceData.totals.total)}</td>
            </tr>
          </tfoot>
        </table>
      </div>
    `;
    resultDiv.style.display = "block";
  }

  function formatCurrency(amount) {
    return new Intl.NumberFormat("he-IL", {
      style: "currency",
      currency: "ILS",
    }).format(amount);
  }
});
