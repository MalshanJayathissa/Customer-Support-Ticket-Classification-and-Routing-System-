export const predictTicket = async (subject, description) => {
  // Simulate backend processing time
  await new Promise((resolve) => setTimeout(resolve, 1200));

  // Temporary mock response
  return {
    category: "Technical Issue",
    team: "Technical Support",
    confidence: 0.94,
    subject,
    description,
  };
};

export const predictBatch = async (tickets) => {
  // Simulate backend processing
  await new Promise((resolve) => setTimeout(resolve, 1500));

  return tickets.map((ticket, index) => ({
    id: index + 1,
    ...ticket,
    category: index % 2 === 0 ? "Technical Issue" : "Account Issue",
    team: index % 2 === 0 ? "Technical Support" : "Account Support",
    confidence: index % 2 === 0 ? 0.94 : 0.89,
  }));
};