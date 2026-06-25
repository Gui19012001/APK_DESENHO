package br.com.suaempresa.testedesenhosmb;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.Locale;
import java.util.Properties;

import jcifs.CIFSContext;
import jcifs.config.PropertyConfiguration;
import jcifs.context.BaseContext;
import jcifs.smb.NtlmPasswordAuthenticator;
import jcifs.smb.SmbFile;

public final class SmbDownloader {

    private SmbDownloader() {
    }

    public static String downloadByCode(
            String server,
            int port,
            String share,
            String remoteFolder,
            String code,
            String domain,
            String username,
            String password,
            String localDirectory
    ) throws Exception {

        Properties properties = new Properties();
        properties.setProperty("jcifs.smb.client.minVersion", "SMB202");
        properties.setProperty("jcifs.smb.client.maxVersion", "SMB311");
        properties.setProperty("jcifs.smb.client.connTimeout", "12000");
        properties.setProperty("jcifs.smb.client.responseTimeout", "30000");
        properties.setProperty("jcifs.smb.client.soTimeout", "35000");
        properties.setProperty("jcifs.smb.client.dfs.disabled", "true");

        CIFSContext baseContext = new BaseContext(
                new PropertyConfiguration(properties)
        );

        NtlmPasswordAuthenticator authenticator =
                new NtlmPasswordAuthenticator(
                        domain == null ? "" : domain,
                        username == null ? "" : username,
                        password == null ? "" : password
                );

        CIFSContext authenticatedContext =
                baseContext.withCredentials(authenticator);

        String normalizedFolder = normalizeFolder(remoteFolder);
        String folderUrl =
                "smb://" + server + ":" + port + "/" + share + "/" +
                encodePath(normalizedFolder) + "/";

        SmbFile directory;

        try {
            directory = new SmbFile(folderUrl, authenticatedContext);

            if (!directory.exists() || !directory.isDirectory()) {
                throw new Exception(
                        "FILE_NOT_FOUND: pasta remota não existe: " + folderUrl
                );
            }
        } catch (jcifs.smb.SmbAuthException authError) {
            throw new Exception(
                    "AUTHENTICATION_FAILED: " + authError.getMessage(),
                    authError
            );
        } catch (Exception connectionError) {
            String message = connectionError.getMessage();

            if (message != null && message.contains("FILE_NOT_FOUND")) {
                throw connectionError;
            }

            throw new Exception(
                    "CONNECTION_FAILED: " + connectionError.getMessage(),
                    connectionError
            );
        }

        String requestedCode = code.trim();
        String exactName = requestedCode.toLowerCase(Locale.ROOT).endsWith(".pdf")
                ? requestedCode
                : requestedCode + ".pdf";

        SmbFile selected = null;
        long selectedModified = Long.MIN_VALUE;

        try {
            SmbFile[] files = directory.listFiles();

            if (files != null) {
                for (SmbFile file : files) {
                    if (file.isFile() &&
                            file.getName().equalsIgnoreCase(exactName)) {
                        selected = file;
                        break;
                    }
                }

                if (selected == null) {
                    String prefix = removePdfExtension(requestedCode)
                            .toLowerCase(Locale.ROOT);

                    for (SmbFile file : files) {
                        String lower = file.getName().toLowerCase(Locale.ROOT);

                        if (file.isFile()
                                && lower.endsWith(".pdf")
                                && lower.startsWith(prefix)) {
                            long modified = file.getLastModified();

                            if (selected == null || modified > selectedModified) {
                                selected = file;
                                selectedModified = modified;
                            }
                        }
                    }
                }
            }
        } catch (jcifs.smb.SmbAuthException authError) {
            throw new Exception(
                    "AUTHENTICATION_FAILED: " + authError.getMessage(),
                    authError
            );
        } catch (Exception listError) {
            throw new Exception(
                    "CONNECTION_FAILED: erro ao listar a pasta: " +
                    listError.getMessage(),
                    listError
            );
        }

        if (selected == null) {
            throw new Exception(
                    "FILE_NOT_FOUND: nenhum PDF iniciado por " +
                    requestedCode + " foi encontrado"
            );
        }

        File targetDirectory = new File(localDirectory);

        if (!targetDirectory.exists() && !targetDirectory.mkdirs()) {
            throw new Exception(
                    "Não foi possível criar a pasta local: " + localDirectory
            );
        }

        String safeName = selected.getName()
                .replaceAll("[\\\\/:*?\"<>|]", "_");

        File localFile = new File(targetDirectory, safeName);

        try (
                InputStream input = selected.getInputStream();
                OutputStream output = new FileOutputStream(localFile, false)
        ) {
            byte[] buffer = new byte[64 * 1024];
            int read;

            while ((read = input.read(buffer)) != -1) {
                output.write(buffer, 0, read);
            }

            output.flush();

        } catch (jcifs.smb.SmbAuthException authError) {
            throw new Exception(
                    "AUTHENTICATION_FAILED: " + authError.getMessage(),
                    authError
            );
        } catch (Exception downloadError) {
            throw new Exception(
                    "CONNECTION_FAILED: erro ao baixar o PDF: " +
                    downloadError.getMessage(),
                    downloadError
            );
        }

        return localFile.getAbsolutePath();
    }

    private static String normalizeFolder(String folder) {
        if (folder == null) {
            return "";
        }

        String value = folder.trim().replace("\\", "/");

        while (value.startsWith("/")) {
            value = value.substring(1);
        }

        while (value.endsWith("/")) {
            value = value.substring(0, value.length() - 1);
        }

        return value;
    }

    private static String removePdfExtension(String value) {
        if (value.toLowerCase(Locale.ROOT).endsWith(".pdf")) {
            return value.substring(0, value.length() - 4);
        }

        return value;
    }

    private static String encodePath(String path) throws Exception {
        String[] segments = path.split("/");
        StringBuilder encoded = new StringBuilder();

        for (int index = 0; index < segments.length; index++) {
            if (index > 0) {
                encoded.append("/");
            }

            encoded.append(
                    URLEncoder.encode(
                            segments[index],
                            StandardCharsets.UTF_8.name()
                    ).replace("+", "%20")
            );
        }

        return encoded.toString();
    }
}
