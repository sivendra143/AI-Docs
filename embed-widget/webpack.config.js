const path = require('path');
const TerserPlugin = require('terser-webpack-plugin');
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');

module.exports = {
  entry: './src/widget-fixed.js',
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'pdf-chat-widget.min.js',
    library: 'PDFChatWidget',
    libraryTarget: 'umd',
    libraryExport: 'default',
    globalObject: 'this',
  },
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'pdf-chat-widget.min.js',
    library: {
      name: 'PDFChatWidget',
      type: 'umd',
      export: 'default',
    },
    globalObject: 'this',
    umdNamedDefine: true
  },
  optimization: {
    minimize: true,
    minimizer: [
      new TerserPlugin({
        terserOptions: {
          format: {
            comments: false,
          },
        },
        extractComments: false,
      }),
      new CssMinimizerPlugin(),
    ],
  },
  performance: {
    hints: false,
    maxEntrypointSize: 512000,
    maxAssetSize: 512000,
  },
  devtool: 'source-map'
};
