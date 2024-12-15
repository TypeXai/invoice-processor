// Firebase Configuration Loader
class FirebaseConfigLoader {
  static async loadConfig() {
    try {
      // In production, fetch from your secure API endpoint
      if (window.location.hostname !== "localhost") {
        const response = await fetch("/api/firebase-config");
        const config = await response.json();
        return config;
      }

      // For local development, use environment variables
      return {
        apiKey: process.env.FIREBASE_API_KEY,
        authDomain:
          process.env.FIREBASE_AUTH_DOMAIN ||
          "invoice-processor-app.firebaseapp.com",
        projectId: process.env.FIREBASE_PROJECT_ID || "invoice-processor-app",
        storageBucket:
          process.env.FIREBASE_STORAGE_BUCKET ||
          "invoice-processor-app.appspot.com",
        messagingSenderId: process.env.FIREBASE_SENDER_ID,
        appId: process.env.FIREBASE_APP_ID,
        measurementId: process.env.FIREBASE_MEASUREMENT_ID,
      };
    } catch (error) {
      console.error("Error loading Firebase config:", error);
      throw error;
    }
  }
}

// Firebase Service Class
class FirebaseService {
  constructor() {
    this.initialized = false;
    this.init();
  }

  async init() {
    try {
      if (this.initialized) return;

      const config = await FirebaseConfigLoader.loadConfig();
      firebase.initializeApp(config);

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

      this.initialized = true;
      console.log("Firebase initialized successfully");

      // Test storage connection
      await this.testStorageConnection();
    } catch (error) {
      console.error("Firebase initialization error:", error);
      throw error;
    }
  }

  async testStorageConnection() {
    try {
      const testRef = this.storage.ref().child("test.txt");
      await testRef.putString("test");
      await testRef.delete();
      console.log("Storage connection successful");
    } catch (error) {
      console.error("Storage connection failed:", error);
      throw error;
    }
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
