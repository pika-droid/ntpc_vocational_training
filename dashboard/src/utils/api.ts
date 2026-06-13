export const getApiBaseUrl = () => {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  if (typeof window !== "undefined") {
    // Dynamically resolve the hostname to support local network access (e.g. 192.168.x.x:3000 -> 192.168.x.x:8000)
    return `http://${window.location.hostname}:8000`;
  }
  return "http://localhost:8000";
};

export const getImageUrl = (url: string) => {
  if (!url) return '';
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url;
  }
  return `${getApiBaseUrl()}${url}`;
};
