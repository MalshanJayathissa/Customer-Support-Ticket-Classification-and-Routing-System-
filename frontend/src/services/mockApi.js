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