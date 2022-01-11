const fsp = require('fs').promises;
const fs = require('fs');
const request = require('request')

const download = (url, path, callback) => {
    request.head(url, (err, res, body) => {
        request(url)
            .pipe(fs.createWriteStream(path))
            .on('close', callback)
    })
}

const url = 'https://storage.googleapis.com/xai-demo-assets/visual-inspection/images/table.jpg'
const dir = './src/assets/'
const filename = 'table.jpg'

fsp.stat(dir).catch(async (err) => {
    if (err.message.includes('no such file or directory')) {
        await fsp.mkdir(dir);
    }
});

fsp.stat(dir + filename).catch(async (err) => {
    download(url, dir + filename, () => {
        console.log('✅ Downloaded image files(s) from xai-demonstrator-assets!')
    })
})
