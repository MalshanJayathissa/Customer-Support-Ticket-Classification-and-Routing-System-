export const dashboardStats = {
  totalPredictions: 1248,
  totalCategories: 6,
  averageConfidence: 91.7,
  successfulRoutes: 1196,
};

export const categoryData = [
  { name: "Technical", value: 340 },
  { name: "Account", value: 260 },
  { name: "Billing", value: 220 },
  { name: "Product", value: 180 },
  { name: "Delivery", value: 150 },
  { name: "Other", value: 98 },
];

export const teamData = [
  { name: "Technical Support", tickets: 340 },
  { name: "Account Support", tickets: 260 },
  { name: "Billing Team", tickets: 220 },
  { name: "Product Support", tickets: 180 },
  { name: "Operations", tickets: 150 },
  { name: "General Support", tickets: 98 },
];

export const recentPredictions = [
  {
    id: "TCK-001",
    subject: "Unable to login",
    category: "Account",
    team: "Account Support",
    confidence: 94.2,
  },
  {
    id: "TCK-002",
    subject: "Payment was charged twice",
    category: "Billing",
    team: "Billing Team",
    confidence: 92.8,
  },
  {
    id: "TCK-003",
    subject: "Application keeps crashing",
    category: "Technical",
    team: "Technical Support",
    confidence: 96.1,
  },
  {
    id: "TCK-004",
    subject: "Order has not arrived",
    category: "Delivery",
    team: "Operations",
    confidence: 88.7,
  },
  {
    id: "TCK-005",
    subject: "Question about product features",
    category: "Product",
    team: "Product Support",
    confidence: 90.4,
  },
];