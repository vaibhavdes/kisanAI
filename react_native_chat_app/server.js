const { createReadStream, existsSync, readFileSync, statSync } = require("node:fs");
const { join, normalize } = require("node:path");
const { createServer } = require("node:http");

const root = join(__dirname, "dist");
const port = Number(process.env.PORT || 8080);

const contentTypes = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".svg": "image/svg+xml",
  ".ico": "image/x-icon",
  ".woff": "font/woff",
  ".woff2": "font/woff2",
};

function fileForUrl(url) {
  const pathname = decodeURIComponent((url || "/").split("?")[0]);
  const safePath = normalize(pathname).replace(/^(\.\.[/\\])+/, "");
  const candidate = join(root, safePath);
  if (existsSync(candidate) && statSync(candidate).isFile()) {
    return candidate;
  }
  return join(root, "index.html");
}

function contentType(file) {
  const dot = file.lastIndexOf(".");
  const ext = dot >= 0 ? file.slice(dot).toLowerCase() : "";
  return contentTypes[ext] || "application/octet-stream";
}

createServer((request, response) => {
  const file = fileForUrl(request.url);
  if (file.endsWith("index.html")) {
    const apiUrl = JSON.stringify(process.env.EXPO_PUBLIC_API_URL || "");
    const html = readFileSync(file, "utf8").replace(
      "</head>",
      `<script>window.KISAN_AI_API_URL=${apiUrl};</script></head>`,
    );
    response.writeHead(200, {
      "Content-Type": "text/html; charset=utf-8",
      "Cache-Control": "no-cache",
    });
    response.end(html);
    return;
  }
  response.writeHead(200, {
    "Content-Type": contentType(file),
    "Cache-Control": file.endsWith("index.html") ? "no-cache" : "public, max-age=31536000, immutable",
  });
  createReadStream(file).pipe(response);
}).listen(port, "0.0.0.0", () => {
  console.log(`Kisan AI frontend listening on ${port}`);
});
