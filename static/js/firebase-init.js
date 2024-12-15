// Firebase initialization and utility functions
class FirebaseService {
  constructor() {
    this.auth = firebase.auth();
    this.storage = firebase.storage();
    this.analytics = firebase.analytics();

    // Monitor auth state
    this.auth.onAuthStateChanged((user) => {
      if (user) {
        console.log("User logged in:", user.email);
        this.analytics.setUserProperties({ userType: "authenticated" });
      }
    });
  }

  // Upload invoice image to Firebase Storage
  async uploadInvoice(file) {
    try {
      const timestamp = Date.now();
      const path = `invoices/${timestamp}_${file.name}`;
      const ref = this.storage.ref().child(path);

      // Log upload start
      this.analytics.logEvent("invoice_upload_start", {
        fileSize: file.size,
        fileType: file.type,
      });

      // Upload file
      const snapshot = await ref.put(file);
      const downloadURL = await snapshot.ref.getDownloadURL();

      // Log successful upload
      this.analytics.logEvent("invoice_upload_success", {
        fileSize: file.size,
        uploadTime: Date.now() - timestamp,
      });

      return downloadURL;
    } catch (error) {
      // Log error
      this.analytics.logEvent("invoice_upload_error", {
        error: error.message,
      });
      throw error;
    }
  }

  // Log processing events
  logProcessing(success, processingTime, errorMessage = null) {
    const eventParams = {
      processingTime,
      timestamp: Date.now(),
    };

    if (success) {
      this.analytics.logEvent("invoice_processing_success", eventParams);
    } else {
      this.analytics.logEvent("invoice_processing_error", {
        ...eventParams,
        error: errorMessage,
      });
    }
  }

  // Track user interactions
  trackInteraction(action, details = {}) {
    this.analytics.logEvent("user_interaction", {
      action,
      timestamp: Date.now(),
      ...details,
    });
  }
}

// Initialize Firebase service
const firebaseService = new FirebaseService();

// Export for use in other scripts
window.firebaseService = firebaseService;
