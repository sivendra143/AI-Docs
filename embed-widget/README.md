# PDF Chat Widget

An embeddable chat widget for the PDF Chat application. This widget can be easily integrated into any website.

## Features

- Easy to embed with just a few lines of code
- Customizable appearance (colors, position, title)
- Responsive design that works on all devices
- Lightweight and fast

## Installation

1. Install dependencies:
   ```bash
   cd embed-widget
   npm install
   ```

2. Build the widget:
   ```bash
   npm run build
   ```

   This will create a minified version of the widget in the `dist` folder.

## Usage

1. Include the widget script in your HTML:
   ```html
   <script src="path/to/pdf-chat-widget.min.js"></script>
   ```

2. Initialize the widget with your configuration:
   ```javascript
   document.addEventListener('DOMContentLoaded', function() {
       const chatWidget = new PDFChatWidget({
           apiUrl: 'http://your-api-url.com', // Your API URL
           position: 'bottom-right', // or 'bottom-left', 'top-right', 'top-left'
           primaryColor: '#4f46e5', // Your brand color
           title: 'Chat with our Assistant' // Custom title
       });
   });
   ```

## Development

For development, you can use the development server with hot reloading:

```bash
npm run dev
```

This will watch for changes in the `src` folder and automatically rebuild the widget.

## Example

Check the `example.html` file for a working example. Open it in a browser to see the widget in action.

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `apiUrl` | String | `window.location.origin` | The base URL of your PDF Chat API |
| `position` | String | `'bottom-right'` | Position of the widget (`'bottom-right'`, `'bottom-left'`, `'top-right'`, or `'top-left'`) |
| `primaryColor` | String | `'#4f46e5'` | Primary color for the widget (any valid CSS color) |
| `title` | String | `'PDF Chat Assistant'` | Title displayed in the widget header |

## Building for Production

To create a production build with minified files:

```bash
npm run build
```

The output will be in the `dist` folder.

## License

MIT
