export async function transcribeAudioDummy(_blob: Blob): Promise<string> {
  // Simulate network latency and a transcription result
  await new Promise((resolve) => setTimeout(resolve, 900));
  return "This is a dummy transcription. You can edit this text before sending.";
}
