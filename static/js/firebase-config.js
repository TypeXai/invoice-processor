// Firebase configuration
const firebaseConfig = {
  apiKey: process.env.FIREBASE_API_KEY || "",
  authDomain: `${
    process.env.FIREBASE_PROJECT_ID || "invoice-processor"
  }.firebaseapp.com`,
  projectId: process.env.FIREBASE_PROJECT_ID || "invoice-processor",
  storageBucket:
    process.env.FIREBASE_STORAGE_BUCKET || "invoice-processor.appspot.com",
  messagingSenderId: process.env.FIREBASE_SENDER_ID || "",
  appId: process.env.FIREBASE_APP_ID || "",
  measurementId: process.env.FIREBASE_MEASUREMENT_ID || "",
};

// Initialize Firebase with error handling
try {
  firebase.initializeApp(firebaseConfig);
  console.log("Firebase initialized successfully");
} catch (error) {
  console.error("Error initializing Firebase:", error);
}

// Initialize Analytics with error handling
try {
  firebase.analytics();
  console.log("Firebase Analytics initialized");
} catch (error) {
  console.error("Error initializing Firebase Analytics:", error);
}
